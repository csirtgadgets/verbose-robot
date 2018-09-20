import os
from setuptools import setup, find_packages
import versioneer
import sys

ENABLE_INSTALL = os.getenv('CIF_ENABLE_INSTALL')

if sys.version_info < (3, 6):
    print("\n")
    print("This requires python 3.6 or higher")
    print("\n")
    raise SystemExit

# vagrant doesn't appreciate hard-linking
if os.environ.get('USER') == 'vagrant' or os.path.isdir('/vagrant'):
    del os.link

if sys.argv[-1] == 'install':
    if not ENABLE_INSTALL:
        print('')
        print('CIFv4 Should NOT be installed using traditional install methods')
        print('Please see the Wiki and use the EasyButton')
        print('the EasyButton uses Ansible to customize the underlying OS and all the moving parts..')
        print('')
        print('https://github.com/csirtgadgets/verbose-robot/wiki')
        print('')
        raise SystemError


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
    r = os.system('py.test test -v --cov=cif --cov-fail-under=45')
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
    license='MPL2',
    classifiers=[
               "Topic :: System :: Networking",
               "Programming Language :: Python",
               ],
    keywords=['security'],
    author="Wes Young",
    author_email="wes@csirtgadgets.com",
    packages=find_packages(),
    install_requires=[],
    scripts=[],
    entry_points={
        'console_scripts': [
            'cif-router=cif.router:main',
            'cif-httpd=cif.httpd.app:main',
            'cif=cifsdk.cli:main',
            'cif-tokens=cifsdk.tokens:main',
            'cif-hunter=cif.hunter:main',
            'cif-gatherer=cif.gatherer:main',
            'cif-store=cif.store:main',
            'cif-streamer=cif.streamer:main'
        ]
    },
)
