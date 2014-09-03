import ldapconnect
from ldaplogging import ldebug
import ldapobject
import ldap
_op_stack = None
running = False


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
        _op_stack.append((1, (func, args, kwargs, old_vals, undo_mod_attr)))
        return func(*args, **kwargs)
    return wrap


def atomic_modrdn(func):
    def undo_modrdn(self, newrdn):
        self._raw_modrdn(newrdn)

    def wrap(*args, **kwargs):
        self = args[0]
        old_vals = (self, ldapobject.dn_to_tuple(self.get_dn())[0][1])
        _op_stack.append((1, (func, args, kwargs, old_vals, undo_modrdn)))
        return func(*args, **kwargs)
    return wrap


def atomic_add(func):
    def undo_add(dn):
        ldapconnect.delete(dn)

    def wrap(*args, **kwargs):
        old_vals = (args[1])
        _op_stack.append((0, (func, args, kwargs, old_vals, undo_add)))
        return func(*args, **kwargs)
    return wrap


def atomic_delete(func):
    def undo_delete(dn, modlist):
        ldapconnect.add(dn, modlist)

    def wrap(*args, **kwargs):
        dn = args[1]
        # Get the object's attributes
        # and demongify it what ldap.add_s wants
        attrs = ldapconnect.search(dn, ldap.SCOPE_BASE, None)[0][1]
        attrlist = [(x, attrs[x][0] if len(attrs[x]) == 1 else attrs[x])
                    for x in attrs]
        old_vals = (dn, attrlist)
        _op_stack.append((0, (func, args, kwargs, old_vals, undo_delete)))
        return func(*args, **kwargs)
    return wrap


def atomic(func):
    global _op_stack
    # initialize the data structures
    if _op_stack is None:
        _op_stack = []

    def wrap(*args, **kwargs):
        print "yoyo"
        global _op_stack
        err = False
        try:
            print "CALLING %s" % func
            ret = func(*args, **kwargs)
        except Exception, e:
            err = True
        # Using exceptions here is crude
        # but the alternative is using queue locking
        if err:
            ldebug("<exception raised in atomic operation... reversing>")
            undo_list = _op_stack.reverse()
            # For each task done
            if undo_list is not None:
                for x in undo_list:
                    ldebug("<executing %s in undo stack>" % x[4])
                    # Call the inverse function with the old values
                    x[4](*x[3])
            # Now that the operations are reversed, re-raise the exception
            raise e
            # Reset the task queue and stack
            _op_stack = []
            # Unlock queue
        return ret
    wrap.__name__ = func.__name__
    wrap.__doc__ = func.__doc__
    return wrap
