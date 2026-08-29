import test_phase2
import test_phase4_billing
import test_phase5_operations

def run_all():
    print("==================================================")
    print("RUNNING ALL ROADSAFE-GPS INTEGRATION TEST SUITES")
    print("==================================================")
    
    print("\n--- RUNNING PHASE 2 DISPATCH TESTS ---")
    test_phase2.run_phase2_dispatch_tests()
    
    print("\n--- RUNNING PHASE 4 BILLING & PAYMENT TESTS ---")
    test_phase4_billing.run_phase4_billing_tests()

    print("\n--- RUNNING PHASE 5 OPERATIONS & REVIEWS TESTS ---")
    test_phase5_operations.run_phase5_operations_tests()

    print("\n==================================================")
    print("ALL ROADSAFE-GPS TEST SUITES PASSED 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    run_all()
