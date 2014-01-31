import Queue
import ldapconnect
from ldaplogging import ldebug
import ldapobject
import ldap
_op_queue = None
_op_stack = None


class Operation(object):

    global _op_queue
    global _op_stack

    def __init__(self, do_func, undo_func, func_args, *args, **kwargs):
        return


def atomic_modattrs(func):

    def undo_mod_attr(self, modlist):
        self._raw_modattrs(modlist)

    def wrap(*args, **kwargs):

        self = args[0]
        # (Modify mode, attribute to modify, new value)
        old_vals = (self,
                    (args[1][0][0], [args[1][0][1]],
                     [self._raw_readattrs([args[1][0][1]])])
                    )

        _op_queue.put((func, args, kwargs, old_vals, undo_mod_attr))
        return

    return wrap


def atomic_modrdn(func):

    def undo_modrdn(self, newrdn):
        self._raw_modrdn(newrdn)

    def wrap(*args, **kwargs):
        self = args[0]

        old_vals = (self, ldapobject.dn_to_tuple(self.get_dn()[0][1]))
        _op_queue.put((func, args, kwargs, old_vals, undo_modrdn))
    return wrap


def atomic_add(func):

    def undo_add(dn):
        ldapconnect.delete(dn)

    def wrap(*args, **kwargs):
        cn = ""
        for x in args[1]:
            if x[0] == "cn":
                cn = x[1]
        dn = ldapconnect.search(
            "dc=netsoc,dc=tcd,dc=ie",
            ldap.SCOPE_SUBTREE, "(cn=%s)" % cn, ['dn']
        )[0][0]

        old_vals = (dn)

        _op_queue.put((func, args, kwargs, old_vals, undo_add))
    return wrap


def atomic_delete(func):

    def undo_delete(dn, modlist):
        ldapconnect.add(dn, modlist)

    def wrap(*args, **kwargs):
        dn = args[0]
        # Get the object's attributes and demongify it what ldap.add_s wants
        attrs = ldapconnect.search(dn, ldap.SCOPE_BASE, None)[0][1]
        attrlist = [(x, attrs[x][0] if len(attrs[x]) == 1 else attrs[x])
                    for x in attrs]
        old_vals = (dn, attrlist)

        _op_queue.put((func, args, kwargs, old_vals, undo_delete))

    return wrap


def atomic(func):
    global _op_queue
    global _op_stack
    # initialize the data structures
    if _op_queue is None:
        _op_queue = Queue.Queue()
    if _op_stack is None:
        _op_stack = []

    def wrap(*args, **kwargs):
        global _op_stack
        global _op_queue

        func(*args, **kwargs)
        err = False
        # Using exceptions here is crude
        # but the alternative is using queue locking
        try:
            # While we haven't run out of intercepted fucntion calls
            while 1:
                func_tuple = _op_queue.get_nowait()
                ldebug("<executing queued job %s with args: %s,%s>" %
                       (func_tuple[0], func_tuple[1], func_tuple[2]))
                try:
                    # Call the functions one after another in succession
                    func_tuple[0](*func_tuple[1], **func_tuple[2])
                except Exception, e:
                    err = True
                    break

                _op_stack.append(func_tuple)

        except Queue.Empty:
            return

        if err:
            ldebug("<exception raised in atomic operation... reversing>")
            undo_list = _op_stack.reverse()
            # For each task done
            for x in undo_list:
                ldebug("<executing %s in undo stack>" % x[4])
                # Call the inverse function with the old values
                x[4](*x[3])
        # Reset the task queue and stack
        _op_stack = []
        _op_queue = Queue.Queue()
        # Now that the operations are reversed, re-raise the exception
        raise e

    return wrap
