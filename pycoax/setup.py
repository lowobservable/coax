import os
from setuptools import setup

ABOUT = {}

with open(os.path.join(os.path.dirname(__file__), "coax", "__about__.py")) as file:
    exec(file.read(), ABOUT)

LONG_DESCRIPTION = """# pycoax

Python IBM 3270 coaxial interface library.

See [GitHub](https://github.com/lowobservable/coax-interface#readme) for more information.
"""

setup(
    name='pycoax',
    version=ABOUT['__version__'],
    description='IBM 3270 coaxial interface',
    url='https://github.com/lowobservable/coax-interface',
    author='Andrew Kay',
    author_email='projects@ajk.me',
    packages=['coax'],
    install_requires=['pyserial==3.4', 'sliplib==0.3.0'],
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Communications',
        'Topic :: Terminals'
    ]
)
