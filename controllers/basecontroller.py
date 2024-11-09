from typing import List, Type
from fastapi import APIRouter

class BaseController:
    """Base controller class that all other controllers will inherit from"""
    
    def __init__(self):
        self.router: APIRouter = APIRouter()
        self.register_routes()

    def register_routes(self):
        """Override this method in child classes to register routes"""
        pass