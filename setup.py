from setuptools import setup, find_packages

setup(
    name='dabanalyzer',
    version='0.0.1',
    description='DAB-chromagen analysis tool',
    longer_description='''
DAB Analyzer counts the stained area with
DAB-chromagen using the typical immunohistochemistry protocols.
After the analysis user can measure the difference of proteins
content in tested samples.
''',
    maintainer='Ivan Gumenyuk',
    maintainer_email='meklon@gmail.com',
    url='https://github.com/meklon/DAB_analyzer',
    namespace_packages=["dabanalyzer"],
    packages=find_packages(exclude=[
        "tests", "tmp", "docs", "data", "test images"]),
    install_requires=[
        'pandas>=0.18.0', 'numpy>=1.11.0', 'scipy',
        'scimage', 'matplotlib', 'seaborn',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
    license='GPLv3',
    classifiers=[
        'Environment :: Console',
    ],
    entry_points={
        'console_scripts': [
            'dabanalyzer = dabanalyzer:main',
        ],
    },
    package_data={
    },)
