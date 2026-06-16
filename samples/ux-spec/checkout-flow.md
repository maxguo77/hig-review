# ShopApp — Checkout Flow Spec (v0.3)

Target: iOS app. This spec describes the flow from launch to order completion.

## 1. Launch & onboarding
1. On first launch, show 5 full-screen tutorial slides explaining every feature.
   The user must view all 5 slides; there is no Skip button.
2. After the tutorial, require the user to create an account and sign in before
   they can browse any products.

## 2. Browse & cart
3. The product list loads from the server. (No loading indicator is specified.)
4. If the user has no items, the cart screen shows nothing.
5. Tapping a product adds it to the cart immediately.

## 3. Permissions
6. Immediately on first launch, request Camera, Location, and Notifications
   permissions together, before showing any UI, so the app has them ready.

## 4. Checkout
7. The checkout screen collects shipping and payment details on one screen.
8. When the user taps "Pay", submit the payment to the server and then show the
   order confirmation screen.
9. The confirmation screen has no navigation bar and no back button; the user
   stays here until they force-quit or tap "Done".

## 5. Account management
10. In Settings, a "Delete account" button permanently deletes the account and
    all order history as soon as it is tapped.

## Notes
- Colors and copy are defined in the design file; not covered here.
- Payment failures: TBD.
