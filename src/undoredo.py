
class UndoRedoAction:
    def __init__(self, function, *args):
        self.function = function
        self.args = args
    def execute(self):
        self.function(*self.args)

class UndoRedoManager:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []
        self.undoing = False

    def pushAction(self, action):
        if self.undoing:
            self.redo_stack.append(action)
        else:
            self.undo_stack.append(action)

    def undo(self):
        if self.undo_stack != []:
            self.undoing = True
            action = self.undo_stack.pop()
            action.execute()
            self.undoing = False
        else:
            print("Nothing to Undo!")

    def redo(self):
        if self.redo_stack != []:
            action = self.redo_stack.pop()
            action.execute()
        else:
            print("Nothing to Redo!")
