#!/usr/bin/env python3

from setuptools import setup

setup(
    name="nrrdalrt",
    version="0.0.2",
    description="Task and event notifications for nrrdtask and nrrddate.",
    author="Sean O'Connell",
    author_email="sean@sdoconnell.net",
    url="https://github.com/sdoconnell/nrrdalrt",
    license="MIT",
    python_requires='>=3.8',
    packages=['nrrdalrt'],
    install_requires=[
        "notify2>=0.3",
        "daemonize>=2.5",
        "python-dateutil>=2.8",
        "tzlocal>=2.1"
    ],
    include_package_data=True,
    entry_points={
        "console_scripts": "nrrdalrt=nrrdalrt.nrrdalrt:main"
    },
    keywords='calendar task notifications',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Topic :: Office/Business',
        'Topic :: Utilities'
    ]
)
