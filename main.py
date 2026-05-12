import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        reload_excludes=[
            ".venv",
            "venv",
            "__pycache__",
            "*.pyc",
            ".git",
            "logs",
            "oilintel.db",
            "eia_weekly_output",
        ],
        log_level="debug",
    )