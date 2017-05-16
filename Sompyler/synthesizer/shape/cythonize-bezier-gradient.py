from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("Sompyler/synthesizer/shape/bezier_gradient.pyx")
)
