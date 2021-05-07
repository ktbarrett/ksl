import nox


@nox.session
def tests(session):
    # install prereqs
    session.install("pytest", "coverage", "pytest-cov")
    # install self
    session.install(".")
    # run tests
    session.run("pytest", "--cov=ksl", "--cov-branch")
