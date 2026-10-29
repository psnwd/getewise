# Mobile SDKs (Android, iOS, React Native, Flutter)

In-app payment UI, no browser redirect. Payment details still arrive on your backend `notify_url` (verify md5sig; see `checkout-api.md`). SDK callbacks only tell the UI what happened.

## Contents
- Common setup: register app package name
- Android (native)
- iOS (native)
- React Native
- Flutter
- Request types supported

## Common setup: register the app (RN, Flutter; check Android/iOS docs too)
Dashboard > Settings > Domains and Credentials > Add Domain/App > choose **App** > enter package name / bundle id (e.g. `lk.bhasha.helakuru`) > Request to Approve. The hash shown is that app's **Merchant Secret**. Live accounts: manual review, up to ~1 business day.

## Android (native)
- Repo: JitPack (`maven { url "https://jitpack.io" }` in `settings.gradle` for AGP 7.1+, or root `build.gradle` older).
- Deps: `com.github.PayHereDevs:payhere-android-sdk:v3.0.18` (version at time of docs), `androidx.appcompat:appcompat:1.6.0`, `com.google.code.gson:gson:2.8.0`.
- Manifest: `INTERNET` permission.
- Build `InitRequest` (setMerchantId, setCurrency, setAmount, setOrderId, setItemsDescription, setCustom1/2, customer name/email/phone/address, optional `setNotifyUrl`, delivery address, `getItems().add(new Item(...))`).
- Recurring: `setRecurrence("1 Month")`, `setDuration("Forever")`, `setStartupFee(0)`.
- Preapproval: use `InitPreapprovalRequest`.
- Hold-on-card: `req.setHoldOnCardEnabled(true)`.
- Launch: `Intent(this, PHMainActivity.class)` with `PHConstants.INTENT_EXTRA_DATA`, `PHConfigs.setBaseUrl(PHConfigs.SANDBOX_URL)` for sandbox, `startActivityForResult(intent, PAYHERE_REQUEST)`.
- Result in `onActivityResult`: read `PHConstants.INTENT_EXTRA_RESULT` as `PHResponse<StatusResponse>`; `response.isSuccess()`.

## iOS (native)
- CocoaPods: `pod 'payHereSDK'`, `platform :ios, '11.0'`, `use_frameworks!`; `import payHereSDK`.
- Build `PHInitialRequest(merchantID:, notifyURL:, firstName:..., orderID:, itemsDescription:, itemsMap:[Item], currency: .LKR, amount:, ...custom1/2)`.
- Recurring adds `startupFee`, `recurrence: .Month(duration: 2)`, `duration: .Forver` (sic: the SDK enum is spelled `Forver`).
- Preapproval: omit amount. Hold on card: `isHoldOnCardEnabled: true`.
- Present: `PHPrecentController.precent(from: self, withInitRequest:, delegate: self)` (sic spelling). Implement `PHViewControllerDelegate`: `onErrorReceived`, `onResponseReceived` (cast data to `payHereSDK.StatusResponse`).

## React Native
- `"@payhere/payhere-mobilesdk-reactnative": "4.0.14"` (docs version), supports RN > 0.60, iOS > 11, Android API > 17.
- Android: add JitPack repo to root gradle; in manifest add `xmlns:tools` and `<application tools:replace="android:allowBackup">`.
- iOS Podfile: `platform :ios, '11.0'`; add `pod 'payHereSDK', :git => 'https://github.com/PayHereDevs/payhere-mobilesdk-ios-rb.git'` and `pod 'payhere-mobilesdk-reactnative', :path => '../node_modules/@payhere/payhere-mobilesdk-reactnative'`; `pod install`.
- Call: `PayHere.startPayment(paymentObject, onCompleted(paymentId), onError(errString), onDismissed())`.
- paymentObject: same keys as web (`sandbox, merchant_id, notify_url, order_id, items, amount, currency, first_name...`). No `merchant_secret` in the RN example.
- Preapproval: `"preapprove": true`. Hold on card: `"authorize": true`. Recurring: `recurrence`, `duration`, `startup_fee`.
- Item-wise: `item_number_1`, `item_name_1`, `amount_1`, `quantity_1`, ...

## Flutter
- `payhere_mobilesdk_flutter: ^3.2.3` (docs version), Flutter > 1.20, iOS > 11, Android API > 17.
- Android: gradle repo is `https://repo.repsy.io/mvn/payhere/payhere-mobilesdk-android/` (not JitPack, unlike RN); manifest `tools:replace="android:label"`; add the documented ProGuard keep rules (retrofit, okhttp, okio, `lk.payhere.**`) for release builds.
- iOS: `pod install`.
- Payment map includes `"merchant_secret"` (the per-app secret from registration) for one-time / recurring / preapproval examples in the docs.
- Same `PayHere.startPayment(map, onCompleted, onError, onDismissed)` signature.
- Older versions: <1.0.2 bintray error fix = upgrade; non-null-safety projects use 1.0.2.

## Security notes
- Mobile apps should not hold App ID/App Secret for the merchant REST APIs. Call those from your backend.
- Merchant secret for apps is per-app; embedding it in the app is how the Flutter SDK works per docs, so treat the app secret as lower trust and always confirm payments server-side via notify + md5sig.
