{
    "version": 2,
    "builds": [
        {
            "src": "*.py",
            "use": "@liudonghua123/now-flask"
        }
    ],
    "routes": [
        {
            "src": "(.*)",
            "dest": "main.py"
        }
    ]
  }