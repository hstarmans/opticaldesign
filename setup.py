from setuptools import find_packages, setup

setup(
    name='prisms',
    package_dir={'': 'src'},
    packages = find_packages(where='src'),
    version='0.0.1',
    description='Optical properties of prisms',
    author='Rik Starmans',
    license='GPLv3',
    project_urls={
        'Blog': 'https://hackaday.io/project/21933-open-hardware-fast-high-resolution-laser',
        'Main page': 'https://www.hexastorm.com',
        'Source': 'https://github.com/hstarmans/prisms',
    }
)