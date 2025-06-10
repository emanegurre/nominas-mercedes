import os
import PyInstaller.__main__


def main():
    """Build executable using the provided PyInstaller spec file."""
    spec_path = os.path.join(os.path.dirname(__file__), 'interfaz_usuario.spec')
    PyInstaller.__main__.run([spec_path])


if __name__ == '__main__':
    main()
