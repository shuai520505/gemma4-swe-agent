# Installed SDK read semantics

kaggle2.2.2 / kagglesdk0.1.35. Audited installed kernels_api_service.py and security/oauth_service.py,not guessed endpoints.

ApiGetKernelRequest fields:user_name,kernel_slug,version_label. No numericID or versionID lookup method is exposed by this installed KernelsApiClient. ApiGetKernelResponse.metadata includes id,ref,author,slug,current_version_number,private/accelerator/model configuration;blob contains source. ListKernels returns metadata rows with resourceIDs,allowing exact-ID search. ListKernels can only provide partial identity when source is inaccessible.

ApiGetKernelSessionStatusRequest and ApiListKernelSessionOutputRequest also expose version_label. Status response contains only status/failure_message;it does not provide run start/end times. Output records contain file_name and signedURL. URLs are used in memory only. The SDK emits HTTP POST for these reads. This is not evidence of mutation. The default status/output target can be latest;we send label1 and bracket output reads with exact latest1/source checks. Neither SDK type support nor mock tests prove server historical-version behavior.

The old collect.py remains unchanged. Its original ACCEPTED_CONFIRMED gate cannot be used after an ambiguous save;this separate path requires live server metadata/source evidence in the same process before enabling downloads. A locally edited acceptance JSON alone cannot enable it.
