"""
00_test_api.py — Wrapper legacy del diagnostico seguro.

Antes este archivo mutaba el modelo (InitializeNewModel/NewBlank/SetStories).
Ahora delega a diag.py para que el "test" sea solo lectura.
"""
import diag


def main():
    diag.main()


if __name__ == '__main__':
    main()
