"""Undo/Redo command system."""
from typing import List, Optional


class Command:
    """Base command class for undo/redo."""
    
    def __init__(self, description: str = ""):
        self.description = description
    
    def execute(self):
        """Execute the command."""
        raise NotImplementedError
    
    def undo(self):
        """Undo the command."""
        raise NotImplementedError
    
    def redo(self):
        """Redo the command."""
        self.execute()


class CommandStack:
    """Command stack for undo/redo operations."""
    
    def __init__(self):
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.callbacks = []
    
    def execute(self, command: Command):
        """Execute a command and add it to undo stack."""
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()
        self._notify()
    
    def undo(self):
        """Undo the last command."""
        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)
            self._notify()
    
    def redo(self):
        """Redo the last undone command."""
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.redo()
            self.undo_stack.append(command)
            self._notify()
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0
    
    def get_undo_description(self) -> Optional[str]:
        """Get the description of the next undo command."""
        if self.undo_stack:
            return self.undo_stack[-1].description
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get the description of the next redo command."""
        if self.redo_stack:
            return self.redo_stack[-1].description
        return None
    
    def register_callback(self, callback):
        """Register a callback for stack changes."""
        self.callbacks.append(callback)
    
    def _notify(self):
        """Notify all callbacks."""
        for callback in self.callbacks:
            callback()
