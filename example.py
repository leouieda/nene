import click

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
def main():
    """
    App description with Unicode ‣
    """
    pass

if __name__ == '__main__':
    main()
