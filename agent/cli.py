#!/usr/bin/env python3
"""
CLI for Network Discovery Agent
"""
import typer

app = typer.Typer()

@app.command()
def list_configs():
    """List scan configurations"""
    typer.echo("Placeholder: list-configs command")

@app.command()
def run(config_id: str):
    """Run a scan for the given config ID"""
    typer.echo(f"Placeholder: run scan for {config_id}")

@app.command()
def schedule():
    """Schedule scans based on config"""
    typer.echo("Placeholder: schedule scans")

if __name__ == "__main__":
    app()
