
#
#  Action-based Undo/Redo
#
# If you want to create an undoable operation, simply write your code.
# At the end, call pushAction() with the function and args needed to undo the function
#
# A call to undo() or redo() will trigger the proper stored functions
#
class UndoRedoManager:

    class Action:
        def __init__(self, function, *args, **kwargs):
            self.function = function
            self.args = args
            self.kwargs = kwargs
        def execute(self):
            self.function(*self.args, **self.kwargs)

    def __init__(self):
        self.reset()

    def reset(self):
        self.undo_stack: list[UndoRedoManager.Action] = []
        self.redo_stack: list[UndoRedoManager.Action] = []
        self.temp_stack: list[UndoRedoManager.Action] = []

    def pushAction(self, function, *args, **kwargs):
        action = UndoRedoManager.Action(function, *args, **kwargs)
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

