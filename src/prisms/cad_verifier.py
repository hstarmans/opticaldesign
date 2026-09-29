"""CAD Optics Verifier for Hexastorm.

Connects to FreeCAD (via XML-RPC on localhost:9875 or direct API), extracts the
global positions of optical components (laser, cylindrical lenses, polygon prism,
folding mirror, photodiode), verifies optical alignment and confocal focal planes,
detects photodiode trigger angles, and pushes key 3D ray geometries into FreeCAD.
"""

import inspect
import json
import logging
import xmlrpc.client
from typing import Any, ClassVar

import prisms.system

logger = logging.getLogger(__name__)


def _get_ray_attr(ray, new_name: str, old_name: str):
    """Retrieve an attribute from a pyoptools Ray supporting modern and legacy APIs."""
    val = getattr(ray, new_name, None)
    if val is not None:
        return val
    return getattr(ray, old_name)


def extract_ray_segments(
    ray, z_offset: float | list[float] = 0.0, max_x: float = 25.0
) -> list[tuple[list[float], list[float]]]:
    """Extract line segments ((x1, y1, z1), (x2, y2, z2)) from a pyoptools ray tree."""
    if isinstance(z_offset, (int, float)):
        offset_xyz = [0.0, 0.0, float(z_offset)]
    else:
        offset_xyz = [float(z_offset[0]), float(z_offset[1]), float(z_offset[2])]

    segments = []
    if getattr(ray, "intensity", 1) == 0:
        return segments

    origin = _get_ray_attr(ray, "origin", "pos")
    p1 = [
        float(origin[0] + offset_xyz[0]),
        float(origin[1] + offset_xyz[1]),
        float(origin[2] + offset_xyz[2]),
    ]

    children = getattr(ray, "childs", []) or getattr(ray, "children", [])
    if len(children) > 0:
        for child in children:
            child_origin = _get_ray_attr(child, "origin", "pos")
            p2 = [
                float(child_origin[0] + offset_xyz[0]),
                float(child_origin[1] + offset_xyz[1]),
                float(child_origin[2] + offset_xyz[2]),
            ]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dz = p2[2] - p1[2]
            if (dx * dx + dy * dy + dz * dz) > 0.01:
                segments.append((p1, p2))
            segments.extend(extract_ray_segments(child, offset_xyz, max_x=max_x))
    else:
        direction = _get_ray_attr(ray, "direction", "dir")
        # For rays striking the photodiode (+X direction), clamp to detector surface
        if direction[0] > 0.5 and (origin[0] + offset_xyz[0]) >= 24.0:
            return segments

        ext_len = 15.0
        if direction[0] > 0.1:
            dist_to_wall = max_x - (origin[0] + offset_xyz[0])
            ext_len = min(ext_len, max(0.0, dist_to_wall / direction[0]))

        if ext_len > 0.05:
            p2 = [
                float(origin[0] + offset_xyz[0] + ext_len * direction[0]),
                float(origin[1] + offset_xyz[1] + ext_len * direction[1]),
                float(origin[2] + offset_xyz[2] + ext_len * direction[2]),
            ]
            segments.append((p1, p2))
    return segments


def _run_in_freecad(client: xmlrpc.client.ServerProxy, func, **kwargs) -> dict:
    """Dispatch a Python worker function to FreeCAD via XML-RPC with JSON kwargs."""
    payload = json.dumps(kwargs)
    src = inspect.getsource(func)
    runner = f"{src}\n{func.__name__}({payload!r})"
    return client.execute_code(runner)


def _freecad_extract_positions(payload_str: str) -> None:
    """Worker executed inside FreeCAD process to extract optical coordinates."""
    import json

    # pyrefly: ignore [missing-import]
    import FreeCAD as App

    payload = json.loads(payload_str)
    doc_name = payload["doc_name"]
    labels = payload["labels"]

    doc = App.getDocument(doc_name)
    if not doc:
        raise ValueError(f"Document {doc_name} is not open in FreeCAD")

    data = {}
    ss = doc.getObject("Spreadsheet001")
    laser_height = float(getattr(ss, "laserheight", 13.0)) if ss else 13.0
    data["laser_height"] = laser_height

    # 1. Polygon Prism
    a4 = doc.getObject("Assembly004")
    doc_mm = App.getDocument("mirrormotor")
    if a4 and doc_mm:
        p_mm = doc_mm.getObject("prism001")
        if p_mm:
            prism_gp = a4.Placement.multiply(p_mm.Placement)
            data["prism"] = [
                float(prism_gp.Base.x),
                float(prism_gp.Base.y),
                float(prism_gp.Base.z + 1.0),
            ]
        else:
            data["prism"] = [0.39, 0.23, laser_height]
    else:
        o_prism = doc.getObject("prism001")
        if o_prism and hasattr(o_prism, "Placement"):
            data["prism"] = [
                float(o_prism.Placement.Base.x),
                float(o_prism.Placement.Base.y),
                laser_height,
            ]
        else:
            data["prism"] = [0.39, 0.23, laser_height]

    # 2. Laser Diode position (queried directly from CAD diode package)
    laser_diode_pos = None
    laser_link = doc.getObject("Laser")
    if laser_link:
        sub_laser = laser_link.getLinkedObject()
        if sub_laser:
            diode_obj = sub_laser.getObject("Laserdiode")
            if diode_obj:
                gp = laser_link.Placement.multiply(diode_obj.Placement)
                laser_diode_pos = [
                    float(gp.Base.x),
                    float(gp.Base.y),
                    float(gp.Base.z),
                ]
    if not laser_diode_pos:
        for item in doc.Objects:
            if (
                "Laserdiode" in getattr(item, "Label", "") or "Laserdiode" in item.Name
            ) and hasattr(item, "Placement"):
                laser_diode_pos = [
                    float(item.Placement.Base.x),
                    float(item.Placement.Base.y),
                    float(item.Placement.Base.z),
                ]
                break
    data["laser"] = laser_diode_pos if laser_diode_pos else [0.0, -58.65, laser_height]

    # 3. Lenses, Mirror, Diode
    for key in ["clens1", "clens2", "mirror", "diode"]:
        lbl = labels.get(key, "")
        o = doc.getObject(lbl)
        if not o:
            matches = doc.getObjectsByLabel(lbl)
            if matches:
                o = matches[0]

        if key == "diode":
            bpw = None
            for item in doc.Objects:
                if "BPW_34" in getattr(item, "Label", "") or "BPW_34" in item.Name:
                    bpw = item
                    break
            if bpw and o:
                gp = o.Placement.multiply(bpw.Placement)
                data[key] = [float(gp.Base.x), float(gp.Base.y), float(gp.Base.z)]
                continue

        if key == "mirror" and o and hasattr(o, "Shape") and o.Shape:
            # Extract the front reflecting surface rather than the 3D solid bounding box center.
            front_face = None
            for f in o.Shape.Faces:
                if f.Area > 50.0:
                    c = f.CenterOfMass
                    uv = f.Surface.parameter(c)
                    n = f.normalAt(uv[0], uv[1])
                    if n.x > 0.4 and n.y < -0.4:
                        front_face = f
                        break
            if front_face:
                c = front_face.CenterOfMass
                data[key] = [float(c.x), float(c.y), float(c.z)]
                continue

        if o:
            if hasattr(o, "Shape") and o.Shape and hasattr(o.Shape, "BoundBox"):
                center = o.Shape.BoundBox.Center
                data[key] = [float(center.x), float(center.y), float(center.z)]
            else:
                gp = (
                    o.getGlobalPlacement()
                    if hasattr(o, "getGlobalPlacement")
                    else getattr(o, "Placement", None)
                )
                if gp is not None:
                    p = gp.Base
                    data[key] = [float(p.x), float(p.y), float(p.z)]
                else:
                    data[key] = None
        else:
            data[key] = None

    print("CAD_POSITIONS:" + json.dumps(data))


def _freecad_push_rays(payload_str: str) -> None:
    """Worker executed inside FreeCAD process to push ray line segments into FreeCAD."""
    import json

    # pyrefly: ignore [missing-import]
    import FreeCAD as App

    # pyrefly: ignore [missing-import]
    import Part

    payload = json.loads(payload_str)
    doc_name = payload["doc_name"]
    segments = payload["segments"]

    doc = App.getDocument(doc_name)
    if not doc:
        raise ValueError(f"Document {doc_name} is not open in FreeCAD")

    sim_grp = doc.getObject("Simulation")
    if not sim_grp:
        sim_grp = doc.addObject("App::DocumentObjectGroup", "Simulation")

    rays_grp = doc.getObject("Rays")
    if not rays_grp:
        rays_grp = doc.addObject("App::DocumentObjectGroup", "Rays")
        sim_grp.addObject(rays_grp)

    for old_obj in list(rays_grp.Group):
        doc.removeObject(old_obj.Name)

    lines = [
        Part.makeLine(App.Base.Vector(*s[0]), App.Base.Vector(*s[1])) for s in segments
    ]
    if lines:
        compound = Part.makeCompound(lines)
        ray_feat = doc.addObject("Part::Feature", "HexastormKeyRays")
        ray_feat.Label = "HexastormKeyRays"
        ray_feat.Shape = compound
        if hasattr(ray_feat, "ViewObject") and ray_feat.ViewObject:
            ray_feat.ViewObject.LineColor = (0.75, 0.0, 0.95, 1.0)
            ray_feat.ViewObject.LineWidth = 3.0
        rays_grp.addObject(ray_feat)

    # Ensure legacy ray groups are hidden to avoid visual duplication
    for legacy in ["Rays005", "Rays006"]:
        lo = doc.getObject(legacy)
        if lo:
            lo.Visibility = False

    doc.recompute()
    print("PUSH_SUCCESS")


class CadOpticsVerifier:
    """Verifies CAD optical geometry and alignment against pyoptools physics."""

    DEFAULT_LABELS: ClassVar[dict[str, str]] = {
        "prism": "Assembly004",
        "clens1": "Clens1_47742",
        "clens2": "CLens2_68048",
        "mirror": "mirror001",
        "laser": "laserdiodebase",
        "diode": "sideplatediode",
    }

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9875,
        doc_name: str = "assembly_compact_new",
        labels: dict[str, str] | None = None,
    ):
        self.host = host
        self.port = port
        self.doc_name = doc_name
        self.labels = labels or self.DEFAULT_LABELS.copy()
        self.rpc_uri = f"http://{host}:{port}"

    def get_client(self) -> xmlrpc.client.ServerProxy:
        return xmlrpc.client.ServerProxy(self.rpc_uri, allow_none=True)

    def extract_cad_positions(self) -> dict[str, list[float] | None]:
        """Extract global (X, Y, Z) coordinates of optical parts from FreeCAD."""
        client = self.get_client()
        res = _run_in_freecad(
            client,
            _freecad_extract_positions,
            doc_name=self.doc_name,
            labels=self.labels,
        )
        msg = res.get("message", "")
        for line in msg.split("\n"):
            if "CAD_POSITIONS:" in line:
                idx = line.find("CAD_POSITIONS:") + len("CAD_POSITIONS:")
                return json.loads(line[idx:].strip())
        raise RuntimeError(f"Could not extract CAD positions from FreeCAD: {res}")

    def verify_and_report(self, update_cad_rays: bool = True) -> dict[str, Any]:
        """Run full alignment verification, confocal plane check, and ray sync."""
        cad_pos = self.extract_cad_positions()

        # Instantiate optical system
        PP = prisms.system.PrismScanner(withcylinder=True)

        results = {
            "cad_positions": cad_pos,
            "alignment": {},
            "focal": {},
            "diode": {},
            "recommendations": [],
        }

        # 1. Laser to Prism alignment (X-axis)
        laser_pos = cad_pos.get("laser")
        prism_pos = cad_pos.get("prism")
        laser_x = laser_pos[0] if laser_pos else 0.0
        prism_x = prism_pos[0] if prism_pos else 0.0
        dx_laser_prism = laser_x - prism_x
        laser_ok = abs(dx_laser_prism) < 0.5
        results["alignment"]["laser_dx"] = dx_laser_prism
        results["alignment"]["laser_pass"] = laser_ok
        if not laser_ok:
            results["recommendations"].append(
                f"Laser is offset from prism center by {dx_laser_prism:+.3f} mm in X."
            )

        # 2. Cylinder Lens 1 centering (X-axis)
        cl1_pos = cad_pos.get("clens1")
        cl1_x = cl1_pos[0] if cl1_pos else 0.0
        dx_cl1_prism = cl1_x - prism_x
        cl1_ok = abs(dx_cl1_prism) < 0.25
        results["alignment"]["cl1_dx"] = dx_cl1_prism
        results["alignment"]["cl1_pass"] = cl1_ok
        if not cl1_ok:
            results["recommendations"].append(
                f"CLens1 is offset from prism center by {dx_cl1_prism:+.3f} mm in X."
            )

        # 3. Confocal focal plane check
        if cl1_pos and prism_pos:
            cl1_y = cl1_pos[1] - prism_pos[1]
            cl1_x = cl1_pos[0] - prism_pos[0]
            PP.set_orientation("CL1", position=[cl1_x, cl1_y, 0])

        cl2_pos = cad_pos.get("clens2")
        if cl2_pos and prism_pos:
            cl2_y = cl2_pos[1] - prism_pos[1]
            cl2_x = cl2_pos[0] - prism_pos[0]
            PP.set_orientation("CL2", position=[cl2_x, cl2_y, 0])

        mirror_pos = cad_pos.get("mirror")
        if mirror_pos and prism_pos:
            mirror_x = mirror_pos[0] - prism_pos[0]
            mirror_y = mirror_pos[1] - prism_pos[1]
            PP.set_orientation("mirror", position=[mirror_x, mirror_y, 0])

        diode_pos = cad_pos.get("diode")
        if diode_pos and prism_pos:
            diode_x = diode_pos[0] - prism_pos[0]
            diode_y = diode_pos[1] - prism_pos[1]
            if (diode_x**2 + diode_y**2) > 100.0:
                PP.set_orientation("diode", position=[diode_x, diode_y, 0])

        f1 = float(PP.focal_point(cyllens1=True))
        f2 = float(PP.focal_point(cyllens1=False))
        delta_f = f1 - f2
        focal_ok = abs(delta_f) < 0.1
        results["focal"]["cl1_focal_x"] = f1
        results["focal"]["cl2_focal_z"] = f2
        results["focal"]["delta_f"] = delta_f
        results["focal"]["confocal_pass"] = focal_ok

        if not focal_ok:
            direction = "decrease" if delta_f > 0 else "increase"
            results["recommendations"].append(
                f"Distance between CLens2 and CLens1 should {direction} by {abs(delta_f):.2f} mm."
            )

        # 4. Photodiode hit angle range
        hit_angles = PP.find_object("diode")
        if hit_angles:
            results["diode"]["hit"] = True
            results["diode"]["angle_range"] = [
                float(hit_angles[0]),
                float(hit_angles[1]),
            ]
        else:
            results["diode"]["hit"] = False
            results["diode"]["angle_range"] = None
            results["recommendations"].append(
                "Photodiode is NOT hit by the laser at current orientation!"
            )

        # 5. Push 3D Rays to FreeCAD
        if update_cad_rays:
            laser_h = cad_pos.get("laser_height", 13.0)
            offset_xyz = [
                prism_pos[0] if prism_pos else 0.0,
                prism_pos[1] if prism_pos else 0.0,
                laser_h,
            ]
            if laser_pos and prism_pos:
                PP.ray_prop["pos"] = [
                    laser_pos[0] - prism_pos[0],
                    laser_pos[1] - prism_pos[1],
                    0.0,
                ]

            PP.draw_key_rays(scanline=True, diode=True)
            segments = []
            for ray in PP.S.prop_ray:
                segments.extend(extract_ray_segments(ray, z_offset=offset_xyz))

            self._push_rays_to_freecad(segments)
            results["rays_pushed_count"] = len(segments)

        return results

    def _push_rays_to_freecad(
        self, segments: list[tuple[list[float], list[float]]]
    ) -> None:
        """Push line segments to FreeCAD as a Part compound in Simulation/Rays."""
        client = self.get_client()
        res = _run_in_freecad(
            client,
            _freecad_push_rays,
            doc_name=self.doc_name,
            segments=segments,
        )
        if "PUSH_SUCCESS" not in res.get("message", ""):
            logger.warning("Failed to push rays to FreeCAD: %s", res)

    def print_report(self, results: dict[str, Any]) -> None:
        """Print a clean Markdown / plain text report of the verification results."""
        pos = results["cad_positions"]
        align = results["alignment"]
        focal = results["focal"]
        diode = results["diode"]
        recs = results["recommendations"]

        print("\n" + "=" * 55)
        print("        HEXASTORM CAD OPTICS VERIFICATION REPORT        ")
        print("=" * 55)

        print("\n1. Extracted Component Global Coordinates (FreeCAD):")
        for k, v in pos.items():
            if k == "laser_height":
                print(f"   {k:12s}: Z = {float(v):7.2f} mm  (Spreadsheet001)")
            elif isinstance(v, (list, tuple)) and len(v) >= 3:
                print(
                    f"   {k:12s}: X = {v[0]:7.2f} mm,  Y = {v[1]:7.2f} mm,  Z = {v[2]:7.2f} mm"
                )
            else:
                print(f"   {k:12s}: [NOT FOUND]")

        print("\n2. Alignment Verification:")
        status_laser = "PASS" if align.get("laser_pass") else "MISALIGNED"
        print(
            f"   • Laser to Prism X-axis alignment : ΔX = {align.get('laser_dx', 0.0):+.3f} mm  [{status_laser}]"
        )
        status_cl1 = "PASS" if align.get("cl1_pass") else "MISALIGNED"
        print(
            f"   • CLens1 to Prism X-centering     : ΔX = {align.get('cl1_dx', 0.0):+.3f} mm  [{status_cl1}]"
        )

        print("\n3. Focal Plane Analysis (Confocal Condition):")
        print(
            f"   • CLens1 Focal Position (X-plane) : {focal.get('cl1_focal_x', 0.0):.2f} mm"
        )
        print(
            f"   • CLens2 Focal Position (Z-plane) : {focal.get('cl2_focal_z', 0.0):.2f} mm"
        )
        status_focal = "PASS" if focal.get("confocal_pass") else "ADJUSTMENT NEEDED"
        print(
            f"   • Focal Distance Mismatch (Δf)    : {focal.get('delta_f', 0.0):+.2f} mm  [{status_focal}]"
        )

        print("\n4. Photodiode Trigger Detection:")
        if diode.get("hit"):
            rng = diode.get("angle_range", [0, 0])
            print(
                f"   • Diode Trigger Window            : {rng[0]:.2f}° to {rng[1]:.2f}°  [HIT DETECTED]"
            )
        else:
            print(
                "   • Diode Trigger Window            : [NOT HIT] - Laser does not strike diode!"
            )

        if recs:
            print("\n5. Recommendations & Actions:")
            for r in recs:
                print(f"   ► {r}")
        else:
            print(
                "\n5. Recommendations & Actions:\n   ► Optical alignment is within design tolerances."
            )

        if "rays_pushed_count" in results:
            print("\n6. FreeCAD Synchronization:")
            print(
                f"   • Pushed {results['rays_pushed_count']} key ray segments to 'Simulation/Rays'."
            )

        print("=" * 55 + "\n")


def verify_cad_optics(
    doc_name: str = "assembly_compact_new", update_cad_rays: bool = True
) -> dict[str, Any]:
    """Convenience function to run verification and print report."""
    verifier = CadOpticsVerifier(doc_name=doc_name)
    results = verifier.verify_and_report(update_cad_rays=update_cad_rays)
    verifier.print_report(results)
    return results


if __name__ == "__main__":
    verify_cad_optics()
