"""Setup file for PyPi."""
import io
import setuptools

def setup():
    """Setup function for PyPi."""
    with io.open('README.rst', 'r', encoding='utf-8') as fp:
        readme = fp.read()

    setuptools.setup(
        name='check-reserved-instances',
        license='BSD',
        description=(
            'Compare instance reservations and running instances for AWS '
            'services'),
        long_description=readme + '\n',
        author='Terbium Labs',
        author_email='developers@terbiumlabs.com',
        url='https://github.com/TerbiumLabs/check-reserved-instances',
        keywords=(
            'ec2 elasticache rds aws reserved instances amazon web services'),
        platforms=['Any'],
        packages=setuptools.find_packages('src'),
        package_dir={'': 'src'},
        use_scm_version=True,
        setup_requires=['setuptools_scm'],
        include_package_data=True,
        zip_safe=False,
        install_requires=[
            'boto3 >= 1.4.4',
            'click',
            'configparser',
            'Jinja2',
            'MarkupSafe'
        ],
        tests_require=[
            'mock',
            'pytest',
            'pytest-cov'
        ],
        entry_points={
            'console_scripts': ['check-reserved-instances = '
                                'check_reserved_instances:cli']
        },
        package_data={
            '': ['LICENSE'],
            'check_reserved_instances':
                ['check_reserved_instances/templates/*.html'],
        },
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'License :: OSI Approved :: BSD License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
        ]
    )

if __name__ == '__main__':
    setup()
