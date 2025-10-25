
class UndoRedoManager:

    class UndoRedoAction:
        def __init__(self, function, *args, **kwargs):
            self.function = function
            self.args = args
            self.kwargs = kwargs
        def execute(self):
            self.function(*self.args, **self.kwargs)

    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def pushAction(self, function, *args, **kwargs):
        action = UndoRedoManager.UndoRedoAction(function, *args, **kwargs)
        # This is the logic for executing a push outside of undo() or redo()
        # but I have saved the redo_stack in case we are in undo() or redo(),
        # if so, we will fix this during the end of undo() or redo()
        self.temp_stack = self.redo_stack.copy()
        self.redo_stack = []
        self.undo_stack.append(action)

    def undo(self):
        if self.undo_stack != []:
            self.undo_stack.pop().execute()
            # We need the redo stack, bring it back
            self.redo_stack = self.temp_stack.copy()
            self.temp_stack = []
            # Now move the action we pushed to the undo stack to the redo stack instead
            # Thats where it needs to go
            self.redo_stack.append(self.undo_stack.pop())
        else:
            print("Nothing to Undo!")

    def redo(self):
        if self.redo_stack != []:
            self.redo_stack.pop().execute()
            # We need the redo stack, bring it back
            self.redo_stack = self.temp_stack.copy()
            self.temp_stack = []
        else:
            print("Nothing to Redo!")

