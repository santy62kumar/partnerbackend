# FastAPI Project Setup Guide

## 1. Create Virtual Environment

```
python -m venv venv
```

## 2. Activate the Virtual Environment

```
venv/Scripts/activate
```

## 3. Fix Security Error (Windows PowerShell)

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 4. Install Dependencies

```
pip install fastapi uvicorn
```

## 5. Create Requirements File

```
pip freeze > requirements.txt
```

## 6. Run FastAPI Server

```
uvicorn app.main:app --reload
```
