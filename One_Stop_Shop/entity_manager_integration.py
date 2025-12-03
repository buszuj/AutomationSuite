"""
Integration example for Entity Manager GUI in One_Stop_Shop
"""

import customtkinter as ctk
from gui.entity_manager_gui import open_entity_manager


def add_entity_manager_to_menu(main_app):
    """
    Add Entity Manager to the main application menu
    
    Args:
        main_app: Main application instance with menu
    """
    # This is an example of how to integrate the entity manager
    # You can add a button or menu item that calls:
    # open_entity_manager(main_app.window)
    pass


# Standalone test
if __name__ == "__main__":
    from gui.entity_manager_gui import EntityManagerGUI
    
    app = EntityManagerGUI()
    app.run()
