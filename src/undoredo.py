
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
from typing import Callable, Any

class UndoRedoManager:

    class Action:
        def __init__(self, function: Callable, *args: str, **kwargs: int) -> None:
            self.function = function
            self.args = args
            self.kwargs = kwargs
        def execute(self) -> Any:
            return self.function(*self.args, **self.kwargs)
        def dump(self) -> None:
            print(self.function, self.args, self.kwargs)

    class Mode(Enum):
        DOING = 1,
        UNDOING = 2,
        REDOING = 3

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.undo_stack: list[UndoRedoManager.Action] = []
        self.redo_stack: list[UndoRedoManager.Action] = []
        self.mode = UndoRedoManager.Mode.DOING

    def pushAction(self, function: Callable, *args, **kwargs) -> None:
        action = UndoRedoManager.Action(function, *args, **kwargs)
        if self.mode == UndoRedoManager.Mode.DOING:
            if self.redo_stack != []:
                self.redo_stack.clear()
            self.undo_stack.append(action)
        elif self.mode == UndoRedoManager.Mode.UNDOING:
            self.redo_stack.append(action)
        elif self.mode == UndoRedoManager.Mode.REDOING:
            self.undo_stack.append(action)

    def pushEndMark(self, desc = "Undescribed") -> None:
        if self.mode == UndoRedoManager.Mode.DOING:
            if self.undo_stack != []:
                if self.undo_stack[-1].function == self.endMarkFunction:
                    raise RuntimeError('UndoRedoManager: pushEndMark without Action(s)')
            self.pushAction(self.endMarkFunction, desc)

    def undo(self) -> str:
        return self.__undoOrRedo('Undo', UndoRedoManager.Mode.UNDOING, self.undo_stack)

    def redo(self) -> str:
        return self.__undoOrRedo('Redo', UndoRedoManager.Mode.REDOING, self.redo_stack)

    def endMarkFunction(self, desc: str) -> str:
        return desc

    # Note: Undo and Redo are the same code, except for the mode and the stacks involved
    def __undoOrRedo(self, opname: str, mode: Mode, stack: list[UndoRedoManager.Action]) -> str:
        self.mode = mode
        if stack != []:
            endaction = stack.pop()
            if endaction.function != self.endMarkFunction: # this shouldn't happen
                msg = f'UndoRedoManager: {opname}ing without Mark!'
                raise RuntimeError(msg)
            desc = endaction.execute()
            done = False
            while not done:
                if stack == []: # this shouldn't happen
                    msg = f'UndoRedoManager: {opname}ing with no Action!'
                    raise RuntimeError(msg)
                if stack[-1].function == self.endMarkFunction:
                    done = True
                else:
                    stack.pop().execute()
                    if stack == []:
                        done = True
            self.pushAction(self.endMarkFunction, desc)
            rv = desc
        else:
            rv = '' # nothing done
        self.mode = UndoRedoManager.Mode.DOING
        return rv




