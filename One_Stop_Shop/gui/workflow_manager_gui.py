"""
Account & Workflow Manager GUI
Manages accounts and their workflows
"""

import customtkinter as ctk
from tkinter import messagebox
import sys
from pathlib import Path

# Add Core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Core"))
from account_workflow_manager import AccountWorkflowManager


class WorkflowManagerGUI:
    """GUI for managing accounts and workflows"""
    
    def __init__(self, parent=None):
        if parent:
            self.window = ctk.CTkToplevel(parent)
        else:
            self.window = ctk.CTk()
        
        self.window.title("Account & Workflow Manager")
        self.window.geometry("1200x700")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.manager = AccountWorkflowManager()
        self.selected_account = None
        self.selected_workflow = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # Title
        title_label = ctk.CTkLabel(
            self.window,
            text="Account & Workflow Manager",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=20)
        
        # Main container with three columns
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Left: Accounts
        self.setup_accounts_panel(main_frame)
        
        # Middle: Workflows
        self.setup_workflows_panel(main_frame)
        
        # Right: Services
        self.setup_services_panel(main_frame)
    
    def setup_accounts_panel(self, parent):
        """Setup accounts panel (left)"""
        accounts_frame = ctk.CTkFrame(parent)
        accounts_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Header
        header = ctk.CTkLabel(
            accounts_frame,
            text="Accounts",
            font=("Arial", 18, "bold")
        )
        header.pack(pady=(10, 5))
        
        # Add button
        add_btn = ctk.CTkButton(
            accounts_frame,
            text="➕ New Account",
            command=self.create_account_dialog,
            height=35
        )
        add_btn.pack(pady=10, padx=20, fill="x")
        
        # Accounts list
        self.accounts_list = ctk.CTkScrollableFrame(accounts_frame)
        self.accounts_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.refresh_accounts()
    
    def setup_workflows_panel(self, parent):
        """Setup workflows panel (middle)"""
        workflows_frame = ctk.CTkFrame(parent)
        workflows_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Header
        self.workflows_header = ctk.CTkLabel(
            workflows_frame,
            text="Workflows",
            font=("Arial", 18, "bold")
        )
        self.workflows_header.pack(pady=(10, 5))
        
        # Add button
        self.add_workflow_btn = ctk.CTkButton(
            workflows_frame,
            text="➕ New Workflow",
            command=self.create_workflow_dialog,
            height=35,
            state="disabled"
        )
        self.add_workflow_btn.pack(pady=10, padx=20, fill="x")
        
        # Workflows list
        self.workflows_list = ctk.CTkScrollableFrame(workflows_frame)
        self.workflows_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Info label
        self.workflows_info = ctk.CTkLabel(
            self.workflows_list,
            text="← Select an account",
            font=("Arial", 12),
            text_color="gray"
        )
        self.workflows_info.pack(pady=50)
    
    def setup_services_panel(self, parent):
        """Setup services panel (right)"""
        services_frame = ctk.CTkFrame(parent)
        services_frame.pack(side="left", fill="both", expand=True)
        
        # Header
        self.services_header = ctk.CTkLabel(
            services_frame,
            text="Services",
            font=("Arial", 18, "bold")
        )
        self.services_header.pack(pady=(10, 5))
        
        # Services list
        self.services_list = ctk.CTkScrollableFrame(services_frame)
        self.services_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Info label
        self.services_info = ctk.CTkLabel(
            self.services_list,
            text="← Select a workflow",
            font=("Arial", 12),
            text_color="gray"
        )
        self.services_info.pack(pady=50)
    
    # Account Management
    def refresh_accounts(self):
        """Refresh accounts list"""
        # Clear
        for widget in self.accounts_list.winfo_children():
            widget.destroy()
        
        accounts = self.manager.get_accounts()
        
        if not accounts:
            label = ctk.CTkLabel(
                self.accounts_list,
                text="No accounts yet",
                text_color="gray"
            )
            label.pack(pady=20)
            return
        
        for account_name in accounts:
            self.create_account_card(account_name)
    
    def create_account_card(self, account_name):
        """Create an account card"""
        card = ctk.CTkFrame(self.accounts_list)
        card.pack(fill="x", pady=5, padx=5)
        
        # Account info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=account_name,
            font=("Arial", 14, "bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")
        
        workflows = self.manager.get_workflows(account_name)
        count_label = ctk.CTkLabel(
            info_frame,
            text=f"{len(workflows)} workflow(s)",
            font=("Arial", 11),
            text_color="gray",
            anchor="w"
        )
        count_label.pack(anchor="w")
        
        # Buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        
        select_btn = ctk.CTkButton(
            btn_frame,
            text="Select",
            command=lambda a=account_name: self.select_account(a),
            width=80,
            height=28
        )
        select_btn.pack(side="left", padx=2)
        
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️",
            command=lambda a=account_name: self.delete_account(a),
            width=40,
            height=28,
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        delete_btn.pack(side="left", padx=2)
    
    def create_account_dialog(self):
        """Show dialog to create account"""
        dialog = ctk.CTkInputDialog(
            text="Enter account name:",
            title="Create Account"
        )
        account_name = dialog.get_input()
        
        if account_name:
            if self.manager.create_account(account_name):
                messagebox.showinfo("Success", f"Account '{account_name}' created!")
                self.refresh_accounts()
            else:
                messagebox.showerror("Error", f"Account '{account_name}' already exists!")
    
    def delete_account(self, account_name):
        """Delete an account"""
        workflows = self.manager.get_workflows(account_name)
        
        confirm = messagebox.askyesno(
            "Delete Account",
            f"Delete account '{account_name}'?\n\n"
            f"This will also delete {len(workflows)} workflow(s).\n\n"
            f"This action cannot be undone!"
        )
        
        if confirm:
            self.manager.delete_account(account_name)
            messagebox.showinfo("Success", f"Account '{account_name}' deleted!")
            
            if self.selected_account == account_name:
                self.selected_account = None
                self.refresh_workflows()
            
            self.refresh_accounts()
    
    def select_account(self, account_name):
        """Select an account to view workflows"""
        self.selected_account = account_name
        self.selected_workflow = None
        self.workflows_header.configure(text=f"Workflows - {account_name}")
        self.add_workflow_btn.configure(state="normal")
        self.refresh_workflows()
    
    # Workflow Management
    def refresh_workflows(self):
        """Refresh workflows list"""
        # Clear
        for widget in self.workflows_list.winfo_children():
            widget.destroy()
        
        if not self.selected_account:
            self.workflows_info = ctk.CTkLabel(
                self.workflows_list,
                text="← Select an account",
                font=("Arial", 12),
                text_color="gray"
            )
            self.workflows_info.pack(pady=50)
            self.refresh_services()
            return
        
        workflows = self.manager.get_workflows(self.selected_account)
        
        if not workflows:
            label = ctk.CTkLabel(
                self.workflows_list,
                text="No workflows yet",
                text_color="gray"
            )
            label.pack(pady=20)
            return
        
        for workflow_name, services in workflows.items():
            self.create_workflow_card(workflow_name, services)
    
    def create_workflow_card(self, workflow_name, services):
        """Create a workflow card"""
        card = ctk.CTkFrame(self.workflows_list)
        card.pack(fill="x", pady=5, padx=5)
        
        # Workflow info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=workflow_name,
            font=("Arial", 13, "bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")
        
        count_label = ctk.CTkLabel(
            info_frame,
            text=f"{len(services)} service(s)",
            font=("Arial", 10),
            text_color="gray",
            anchor="w"
        )
        count_label.pack(anchor="w")
        
        # Buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        
        select_btn = ctk.CTkButton(
            btn_frame,
            text="Select",
            command=lambda w=workflow_name: self.select_workflow(w),
            width=80,
            height=28
        )
        select_btn.pack(side="left", padx=2)
        
        edit_btn = ctk.CTkButton(
            btn_frame,
            text="✏️",
            command=lambda w=workflow_name: self.edit_workflow(w),
            width=40,
            height=28,
            fg_color="#3498db"
        )
        edit_btn.pack(side="left", padx=2)
        
        clone_btn = ctk.CTkButton(
            btn_frame,
            text="📋",
            command=lambda w=workflow_name: self.clone_workflow_dialog(w),
            width=40,
            height=28,
            fg_color="#9b59b6",
            hover_color="#8e44ad"
        )
        clone_btn.pack(side="left", padx=2)
        
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️",
            command=lambda w=workflow_name: self.delete_workflow(w),
            width=40,
            height=28,
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        delete_btn.pack(side="left", padx=2)
    
    def create_workflow_dialog(self):
        """Show dialog to create workflow"""
        if not self.selected_account:
            return
        
        # Create dialog window
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Create Workflow")
        dialog.geometry("500x600")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Workflow name
        ctk.CTkLabel(dialog, text="Workflow Name:", font=("Arial", 14)).pack(pady=(20, 5))
        name_entry = ctk.CTkEntry(dialog, width=400)
        name_entry.pack(pady=5)
        
        # Services selection
        ctk.CTkLabel(dialog, text="Select Services:", font=("Arial", 14)).pack(pady=(20, 5))
        
        services_frame = ctk.CTkScrollableFrame(dialog, width=400, height=350)
        services_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        checkboxes = {}
        for service in self.manager.tpus_services:
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(services_frame, text=service, variable=var)
            cb.pack(anchor="w", pady=2)
            checkboxes[service] = var
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def save_workflow():
            workflow_name = name_entry.get().strip()
            if not workflow_name:
                messagebox.showerror("Error", "Workflow name cannot be empty!")
                return
            
            selected_services = [s for s, var in checkboxes.items() if var.get()]
            if not selected_services:
                messagebox.showerror("Error", "Select at least one service!")
                return
            
            if self.manager.create_workflow(self.selected_account, workflow_name, selected_services):
                messagebox.showinfo("Success", f"Workflow '{workflow_name}' created!")
                dialog.destroy()
                self.refresh_workflows()
            else:
                messagebox.showerror("Error", f"Workflow '{workflow_name}' already exists!")
        
        ctk.CTkButton(btn_frame, text="Create", command=save_workflow, width=100).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy, width=100).pack(side="left", padx=5)
    
    def edit_workflow(self, workflow_name):
        """Edit an existing workflow"""
        services = self.manager.get_workflow_services(self.selected_account, workflow_name)
        
        # Create dialog
        dialog = ctk.CTkToplevel(self.window)
        dialog.title(f"Edit Workflow: {workflow_name}")
        dialog.geometry("500x600")
        dialog.transient(self.window)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=f"Editing: {workflow_name}", font=("Arial", 16, "bold")).pack(pady=20)
        
        # Services selection
        ctk.CTkLabel(dialog, text="Select Services:", font=("Arial", 14)).pack(pady=(10, 5))
        
        services_frame = ctk.CTkScrollableFrame(dialog, width=400, height=400)
        services_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        checkboxes = {}
        for service in self.manager.tpus_services:
            var = ctk.BooleanVar(value=(service in services))
            cb = ctk.CTkCheckBox(services_frame, text=service, variable=var)
            cb.pack(anchor="w", pady=2)
            checkboxes[service] = var
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def save_changes():
            selected_services = [s for s, var in checkboxes.items() if var.get()]
            if not selected_services:
                messagebox.showerror("Error", "Select at least one service!")
                return
            
            self.manager.update_workflow(self.selected_account, workflow_name, selected_services)
            messagebox.showinfo("Success", f"Workflow '{workflow_name}' updated!")
            dialog.destroy()
            self.refresh_workflows()
            if self.selected_workflow == workflow_name:
                self.refresh_services()
        
        ctk.CTkButton(btn_frame, text="Save", command=save_changes, width=100).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy, width=100).pack(side="left", padx=5)
    
    def clone_workflow_dialog(self, workflow_name):
        """Show dialog to clone workflow to another account"""
        if not self.selected_account:
            return
        
        # Get list of other accounts
        all_accounts = self.manager.get_accounts()
        other_accounts = [acc for acc in all_accounts if acc != self.selected_account]
        
        if not other_accounts:
            messagebox.showinfo("No Other Accounts", "Create another account first to clone workflows.")
            return
        
        # Create dialog
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Clone Workflow")
        dialog.geometry("450x300")
        dialog.transient(self.window)
        dialog.grab_set()
        
        ctk.CTkLabel(
            dialog,
            text=f"Clone '{workflow_name}' to:",
            font=("Arial", 16, "bold")
        ).pack(pady=20)
        
        # Target account selection
        ctk.CTkLabel(dialog, text="Select target account:", font=("Arial", 12)).pack(pady=(10, 5))
        
        target_var = ctk.StringVar(value=other_accounts[0])
        account_menu = ctk.CTkOptionMenu(
            dialog,
            variable=target_var,
            values=other_accounts,
            width=300
        )
        account_menu.pack(pady=10)
        
        # New workflow name
        ctk.CTkLabel(dialog, text="New workflow name (optional):", font=("Arial", 12)).pack(pady=(20, 5))
        name_entry = ctk.CTkEntry(dialog, width=300, placeholder_text="Leave empty to keep same name")
        name_entry.pack(pady=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        def perform_clone():
            target_account = target_var.get()
            new_name = name_entry.get().strip()
            new_name = new_name if new_name else None
            
            if self.manager.clone_workflow(self.selected_account, workflow_name, target_account, new_name):
                final_name = new_name if new_name else workflow_name
                messagebox.showinfo(
                    "Success",
                    f"Workflow cloned to '{target_account}' as '{final_name}'!"
                )
                dialog.destroy()
            else:
                final_name = new_name if new_name else workflow_name
                messagebox.showerror(
                    "Error",
                    f"Failed to clone workflow.\n\n"
                    f"Workflow '{final_name}' may already exist in '{target_account}'."
                )
        
        ctk.CTkButton(
            btn_frame,
            text="Clone",
            command=perform_clone,
            width=100,
            fg_color="#9b59b6",
            hover_color="#8e44ad"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100
        ).pack(side="left", padx=5)
    
    def delete_workflow(self, workflow_name):
        """Delete a workflow"""
        confirm = messagebox.askyesno(
            "Delete Workflow",
            f"Delete workflow '{workflow_name}'?\n\n"
            f"This action cannot be undone!"
        )
        
        if confirm:
            self.manager.delete_workflow(self.selected_account, workflow_name)
            messagebox.showinfo("Success", f"Workflow '{workflow_name}' deleted!")
            
            if self.selected_workflow == workflow_name:
                self.selected_workflow = None
                self.refresh_services()
            
            self.refresh_workflows()
    
    def select_workflow(self, workflow_name):
        """Select a workflow to view services"""
        self.selected_workflow = workflow_name
        self.services_header.configure(text=f"Services - {workflow_name}")
        self.refresh_services()
    
    # Services Display
    def refresh_services(self):
        """Refresh services list"""
        # Clear
        for widget in self.services_list.winfo_children():
            widget.destroy()
        
        if not self.selected_workflow:
            self.services_info = ctk.CTkLabel(
                self.services_list,
                text="← Select a workflow",
                font=("Arial", 12),
                text_color="gray"
            )
            self.services_info.pack(pady=50)
            return
        
        services = self.manager.get_workflow_services(self.selected_account, self.selected_workflow)
        
        if not services:
            label = ctk.CTkLabel(
                self.services_list,
                text="No services in workflow",
                text_color="gray"
            )
            label.pack(pady=20)
            return
        
        for i, service in enumerate(services, 1):
            service_frame = ctk.CTkFrame(self.services_list)
            service_frame.pack(fill="x", pady=3, padx=5)
            
            label = ctk.CTkLabel(
                service_frame,
                text=f"{i}. {service}",
                font=("Arial", 12),
                anchor="w"
            )
            label.pack(side="left", padx=15, pady=8)
    
    def run(self):
        """Run the GUI"""
        self.window.mainloop()


if __name__ == "__main__":
    app = WorkflowManagerGUI()
    app.run()
