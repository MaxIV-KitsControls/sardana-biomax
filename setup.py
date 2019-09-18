#!/usr/bin/env python


from setuptools import setup, find_packages


def main():
    """Main method collecting all the parameters to setup."""
    name = "sardana-biomax"

    version = "0.0.0"

    description = "Sardana plugins for the BioMAX beamline at MAX IV."

    author = "MAX IV KITS SW Group"

    author_email = "kitscontrols@maxiv.lu.se"

    license = "LGPLv3"

    url = "http://www.maxiv.lu.se"

    packages = find_packages()

    # Add your dependencies in the following line.
    
    install_requires = ['setuptools', 'sardana']
    
        
    # Add your build requires in the following line.
    
    requires = ['sphinx_rtd_theme', 'pytest', 'setuptools']
    

    setup(
        name=name,
        version=version,
        description=description,
        author=author,
        author_email=author_email,
        license=license,
        url=url,
        packages=packages,
        requires=requires,
        install_requires=install_requires
    )

if __name__ == "__main__":
    main()
