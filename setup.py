from setuptools import setup

with open('requirements.txt') as file:
    install_requires = file.read().split('\n')


setup(
    name='vkms',
    version='0.1.0.dev1',
    python_requires='>=3.6.0',

    author='YariKartoshe4ka',
    author_email='yaroslav.kikel.06@inbox.ru',

    url='https://github.com/YariKartoshe4ka/vk-messages-saver',

    packages=['vkms'],

    entry_points={
        'console_scripts':
            ['vkms = vkms.main:main']
    },

    description='',
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',

    install_requires=install_requires,

    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Topic :: Utilities',
        'Operating System :: OS Independent'
    ],
)
