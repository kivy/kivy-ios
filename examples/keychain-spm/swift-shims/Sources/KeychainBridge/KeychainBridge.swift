import Foundation
import KeychainAccess

/// Objective-C-facing shim over the pure-Swift `KeychainAccess` package.
///
/// `KeychainAccess` exposes a throwing API and Swift subscripts, neither of
/// which pyobjus can call. This class re-exports the three operations the demo
/// needs as `@objc` class methods with flat, Objective-C-representable
/// signatures (`String` <-> `NSString`, `Bool` <-> `BOOL`). The explicit
/// `@objc(...)` selectors keep the names pyobjus looks up stable and avoid
/// clashing with `NSObject`'s key-value-coding methods.
@objc(KeychainBridge)
public final class KeychainBridge: NSObject {
    /// One keychain "service" namespaces this app's items.
    private static func keychain() -> Keychain {
        Keychain(service: "org.kivy.keychain-spm")
    }

    /// Store `value` under `key`. Returns `false` if the keychain write fails.
    @objc(storeString:forKey:)
    public static func store(_ value: String, forKey key: String) -> Bool {
        do {
            try keychain().set(value, key: key)
            return true
        } catch {
            return false
        }
    }

    /// Return the value stored under `key`, or `nil` if absent / on error.
    @objc(stringForKey:)
    public static func string(forKey key: String) -> String? {
        try? keychain().get(key)
    }

    /// Delete the item stored under `key`. Returns `false` if removal fails.
    @objc(deleteKey:)
    public static func delete(_ key: String) -> Bool {
        do {
            try keychain().remove(key)
            return true
        } catch {
            return false
        }
    }
}
