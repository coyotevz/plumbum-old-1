
from plumbum.env import Environment


class EnvironmentStub(Environment):
    """A stub of the plumbum.env.Environment class for testing."""

    required = False
    abstract = True
