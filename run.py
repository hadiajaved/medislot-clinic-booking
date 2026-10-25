"""Development entry point: ``python run.py`` starts the MediSlot server."""
from medislot import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
