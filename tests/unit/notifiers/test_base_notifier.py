import pytest
from notifiers.base_notifier import BaseNotifier
from abc import ABC, abstractmethod


def test_base_notifier_is_abstract():
    """Verify that BaseNotifier cannot be instantiated directly."""
    with pytest.raises(TypeError) as excinfo:
        BaseNotifier()
    assert "Can't instantiate abstract class BaseNotifier" in str(excinfo.value)

def test_derived_class_raises_notimplemented():
    """Verify that an incomplete derived class raises NotImplementedError."""
    
    # Define a concrete class that inherits but implements nothing
    class IncompleteNotifier(BaseNotifier):
        # We need to explicitly implement 'is_configured' to get past the
        # ABC check during instantiation, but leave other methods unimplemented
        # to test the error on call.
        def is_configured(self) -> bool:
            return True
            
        pass
    
    # Instantiate the incomplete class
    notifier = IncompleteNotifier()
    
    # Test all abstract methods raise NotImplementedError
    with pytest.raises(NotImplementedError):
        notifier.send_notification("Title", "Message")
        
    with pytest.raises(NotImplementedError):
        notifier.notify_queue_completed("Queue", 1, 0, 1, "1m")
        
    with pytest.raises(NotImplementedError):
        notifier.notify_queue_failed("Queue", "Error")
        
    with pytest.raises(NotImplementedError):
        notifier.notify_monitoring_update("Playlist", 5)
        
    with pytest.raises(NotImplementedError):
        notifier.notify_size_threshold(100, 150.0)
