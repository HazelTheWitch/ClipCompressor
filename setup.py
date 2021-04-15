import setuptools

packageName = 'compress-clips'

major = 0
minor = 0
micro = 4

pythonVersion = '3.6'

with open('README.md', 'r') as longDescription:
    description = longDescription.read()

setuptools.setup(
    name=f'{packageName}-hazel-trinity',
    version=f'{major}.{minor}.{micro}',
    author='Hazel Trinity',
    description='Compresses video clips into a smaller forms because Nvidia is awful.',
    long_description=description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent'
    ],
    python_requires=f'>={pythonVersion}',
    install_requires=[
        'click',
        'ffmpeg-python',
    ],
    entry_points='''
        [console_scripts]
        compressClips=compressClips.__main__:compressClips
    '''
)
