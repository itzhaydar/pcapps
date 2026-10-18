import sys

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        from glance_guard.diagnostics import run
        run()
    else:
        from glance_guard.app import main
        raise SystemExit(main())
