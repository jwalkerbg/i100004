# cliapp/core.py

def run_app(config):
    """Run the application with the given configuration."""
    if config.get('verbose'):
        print(f"Running in verbose mode. Configuration: {config}")

    # Example functionality based on the configuration
    print(f"Greeting: Hello, {config['name']}!")
