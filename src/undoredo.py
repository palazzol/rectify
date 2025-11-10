
#
#  Action-based Undo/Redo
#
# If you want to create an undoable operation, simply write your code.
# For any undoable operation, call pushAction() with the function and args needed to undo the function
# At the very end of your operation, which may be made of one or more calls to pushAction(), call pushEndMark()
#
# A call to undo() or redo() will trigger the proper stored functions
#

from enum import Enum

class UndoRedoManager:

    class Action:
        def __init__(self, function, *args, **kwargs):
            self.function = function
            self.args = args
            self.kwargs = kwargs
        def execute(self):
            self.function(*self.args, **self.kwargs)

    class Mode(Enum):
        DOING = 1,
        UNDOING = 2,
        REDOING = 3

    def __init__(self):
        self.reset()

    def reset(self):
        self.undo_stack: list[UndoRedoManager.Action] = []
        self.redo_stack: list[UndoRedoManager.Action] = []
        self.mode = UndoRedoManager.Mode.DOING

    def pushAction(self, function, *args, **kwargs):
        action = UndoRedoManager.Action(function, *args, **kwargs)
        if self.mode == UndoRedoManager.Mode.DOING:
            if self.redo_stack != []:
                self.redo_stack.clear()
            self.undo_stack.append(action)
        elif self.mode == UndoRedoManager.Mode.UNDOING:
            self.redo_stack.append(action)
        elif self.mode == UndoRedoManager.Mode.REDOING:
            self.undo_stack.append(action)

    def pushEndMark(self):
        if self.mode == UndoRedoManager.Mode.DOING:
            if self.undo_stack != []:
                if self.undo_stack[-1].function == UndoRedoManager.__endMarkFunction:
                    raise RuntimeError('UndoRedoManager: pushEndMark without Action(s)')
            self.pushAction(UndoRedoManager.__endMarkFunction)

    def undo(self):
        return self.__undoOrRedo('Undo', UndoRedoManager.Mode.UNDOING, self.undo_stack)

    def redo(self):
        return self.__undoOrRedo('Redo', UndoRedoManager.Mode.REDOING, self.redo_stack)

    def __endMarkFunction(self):
        pass

    # Note: Undo and Redo are the same code, except for the mode and the stacks involved
    def __undoOrRedo(self, opname, mode, stack):
        self.mode = mode
        if stack != []:
            action = stack.pop()
            if action.function != UndoRedoManager.__endMarkFunction: # this shouldn't happen
                raise RuntimeError(f'UndoRedoManager: {opname}ing without Mark!')
            done = False
            while not done:
                if stack == []: # this shouldn't happen
                    raise RuntimeError(f'UndoRedoManager: {opname}ing with no Action!')
                if stack[-1].function == UndoRedoManager.__endMarkFunction:
                    done = True
                else:
                    stack.pop().execute()
                    if stack == []:
                        done = True
            self.pushAction(UndoRedoManager.__endMarkFunction)
            return True # operation successful
        else:
            return False # nothing to do
        self.mode = UndoRedoManager.Mode.DOING



