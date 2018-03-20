import os
from setuptools import setup, find_packages
import versioneer
import sys

# vagrant doesn't appreciate hard-linking
if os.environ.get('USER') == 'vagrant' or os.path.isdir('/vagrant'):
    del os.link

# https://www.pydanny.com/python-dot-py-tricks.html
if sys.argv[-1] == 'test':
    test_requirements = [
        'pytest',
        'coverage',
        'pytest_cov',
    ]
    try:
        modules = map(__import__, test_requirements)
    except ImportError as e:
        err_msg = e.message.replace("No module named ", "")
        msg = "%s is not installed. Install your test requirements." % err_msg
        raise ImportError(msg)
    r = os.system('py.test test -v --cov=cif --cov-fail-under=35')
    if r == 0:
        sys.exit()
    else:
        raise RuntimeError('tests failed')

setup(
    name="verbose-robot",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="CIFv4",
    long_description="",
    url="https://github.com/csirtgadgets/verbose-robot",
    license='MPLv2',
    classifiers=[
               "Topic :: System :: Networking",
               "Programming Language :: Python",
               ],
    keywords=['security'],
    author="Wes Young",
    author_email="wes@csirtgadgets.com",
    packages=find_packages(),
    install_requires=[
        'Flask',
        'ujson',
        #'cifsdk>=4.0',
    ],
    scripts=[],
    entry_points={
        'console_scripts': [
            'cif-router=cif.router:main',
            'cif-httpd=cif_httpd.app:main',
            'cif=cifsdk.cli:main',
            'cif-tokens=cifsdk.tokens:main',
            'cif-hunter=cif_hunter:main',
            'cif-gatherer=cif_gatherer:main',
            'cif-store=cif.store:main',
        ]
    },
)
