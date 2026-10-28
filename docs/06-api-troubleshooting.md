# Kiểm tra API DSM, không thay đổi NAS

DSM không có công tắc bật toàn bộ Web API chung. Dịch vụ web DSM cung cấp API discovery/xác thực; các API theo package yêu cầu package tương ứng và quyền tài khoản. Lần kiểm tra mới nhất đã truy cập được NAS SITE, xác minh TLS và thấy API Auth/File Station được công bố. Không cần bật API chung.

## Kiểm tra từ trình duyệt của người quản trị

1. Mở `https://nassite.hbcg.vn:5001` và xác nhận không có cảnh báo chứng chỉ. Không bỏ qua cảnh báo TLS.
2. Mở URL sau, không cần nhập tài khoản vào URL:

```
https://nassite.hbcg.vn:5001/webapi/query.cgi?api=SYNO.API.Info&version=1&method=query&query=SYNO.API.Auth,SYNO.FileStation.Info
```

Kết quả mong đợi: JSON có `success: true`, `data` chứa `SYNO.API.Auth` và, khi được công bố, `SYNO.FileStation.Info` với `minVersion`, `maxVersion`, `path`. API được công bố không chứng minh tài khoản có quyền hoặc mọi chức năng storage/ACL đều khả dụng.

Chỉ gửi lại `success`, tên API, min/maxVersion hoặc mã lỗi. Không gửi cookie, SID, mật khẩu, OTP hay toàn bộ thông tin phiên. Phép thử không thực hiện login, không thay đổi cấu hình, không cần bật SSH/WebDAV.

## Phân loại kết quả

| Quan sát | Hướng kiểm tra tiếp |
|---|---|
| Không mở được trang DSM | DNS, IP public/CGNAT, NAT/port, firewall và đường mạng |
| Cảnh báo chứng chỉ | Tên trên chứng chỉ, thời hạn, full chain và CA tin cậy |
| Trang DSM mở nhưng API ra HTML | Reverse proxy có chuyển `/webapi/` đúng NAS không; có đăng nhập SSO/gateway chặn đường dẫn không |
| HTTP 403/404 từ dịch vụ đích | Reverse proxy/WAF/access policy hoặc đường dẫn; chưa suy ra thiếu API |
| JSON `success: false` | Ghi mã lỗi và API/phương thức đang gọi; đối chiếu tài liệu DSM tương ứng |
| Có Auth nhưng thiếu FileStation.Info | Kiểm tra File Station có được cài và chạy không; kiểm chứng package/API trước khi thay đổi |
| Discovery thành công | Tiếp tục xây/kiểm tra đăng nhập, MFA, quyền tài khoản dịch vụ và logout |
| Chỉ cloud báo proxy refused | Xử lý policy mạng của cloud; kết quả ở máy người dùng và máy ứng dụng có thể khác nhau |

## Kiểm tra trên DSM khi cần

Chỉ xem cấu hình trước, chưa thay đổi:

- DSM 7: Control Panel → Login Portal → DSM: đối chiếu cổng HTTPS thực tế; tên mục có thể khác theo bản DSM/ngôn ngữ.
- Control Panel → Security → Certificate: đối chiếu chứng chỉ được gán cho dịch vụ DSM.
- Package Center: kiểm tra File Station đã cài/đang chạy. Không cài lại chỉ vì một request lỗi.
- User & Group: về sau kiểm tra application permissions và quyền share của tài khoản dịch vụ. Chưa cần cấp admin rộng.
- Nếu có reverse proxy: kiểm tra tuyến tới DSM và `/webapi/`, không thêm bypass xác thực rộng hoặc tắt TLS/firewall.

## CLI hỗ trợ troubleshoot

Chạy từ checkout có dependencies:

```bash
python3 -m backend.diagnose --config config.nassite.example.json --device nas-site
```

Exit code: 0 discovery hợp lệ, 1 inventory/ID sai, 2 phép thử thất bại. Báo cáo có `stage` (proxy/network/tls/http/api), mã lỗi và hướng xử lý. HTTP status chỉ xuất hiện khi có phản hồi HTTP thực tế từ đường request, không gán 403 proxy thành HTTP 403 của NAS. Không nhận credential, không theo redirect, không tắt TLS, không in dữ liệu phiên.

Kết quả mới nhất trong cloud ngày 27/10/2026: discovery `reachable`, TLS được xác minh; `SYNO.API.Auth` 1–7 và `SYNO.FileStation.Info` 1–2 được công bố. Chưa thử xác thực hoặc đọc dữ liệu doanh nghiệp. Lỗi proxy 403 ở các phép thử trước không còn tái hiện trong phép thử CLI mới; chưa có bằng chứng để quy nguyên nhân thay đổi cho thao tác publish cụ thể.

## Bước tiếp theo: kiểm tra đăng nhập/logout có kiểm soát

Đã tải và đọc [DSM Login Web API Guide chính thức](https://global.download.synology.com/download/Document/Software/DeveloperGuide/Os/DSM/All/enu/DSM_Login_Web_API_Guide_enu.pdf). Theo tài liệu: dùng API path do discovery công bố, Auth v6 được khuyến nghị, có OTP, SID và SynoToken. Đã triển khai công cụ kiểm tra riêng, chưa chạy với tài khoản thật:

```bash
python3 -m backend.auth_check --config config.nassite.example.json --device nas-site
```

Chỉ chạy lệnh này trên máy chủ/terminal tin cậy do người quản trị kiểm soát. Công cụ hỏi tài khoản, mật khẩu và OTP tại terminal; mật khẩu/OTP không hiện ra và không chấp nhận qua đối số. Không nhập credential vào chat hoặc console cloud được chia sẻ. Chưa có màn hình quản lý bí mật production; chưa yêu cầu người dùng đưa credential vào cloud.

Một lần login rồi logout ngay. Dùng HTTPS POST body, không đặt mật khẩu/SID/SynoToken vào URL, không ghi log hoặc trả về các giá trị đó. Chỉ giữ phiên trong bộ nhớ; không tạo trusted device hoặc né MFA. Không retry tự động nếu sai mật khẩu/MFA hoặc timeout; timeout đăng nhập có thể đã tạo phiên, cần kiểm tra DSM Sessions. Nếu logout chưa được xác nhận, báo `unconfirmed`, không báo hoàn tất. Kết quả đăng nhập thành công chưa xác minh quyền file/storage.

18 kiểm thử backend đạt, gồm login/logout dùng response mock, từ chối đăng nhập, thiếu SID và lỗi logout. Chưa dùng credential NAS thật; vẫn cần kiểm chứng MFA/quyền trên thiết bị và triển khai kho bí mật/RBAC trước vận hành production.

## Chạy bằng secret của môi trường GPT

Đã khai báo hai secret `NAS_SITE_ACCOUNT`, `NAS_SITE_PASSWORD` chỉ cho đích `nassite.hbcg.vn`. Công cụ không tự có giá trị: người dùng nhập trong Environment Settings → Secrets, lưu và publish theo UI. Khi kiểm tra gần nhất, cả hai binding chưa có giá trị lưu (`has_saved_binding: false`) và chưa xuất hiện trong runtime; chưa có login thật.

Sau khi được cấp secret, chạy `python3 -m backend.cloud_auth_check`: đích cố định NAS SITE, không nhận URL từ secret, không in giá trị, không nhận credential qua chat/đối số, một login/logout và không retry tự động. Nếu thiếu binding, không gọi mạng. Proxy có thể cấp placeholder; dùng qua HTTPS đúng đích, không tự coi placeholder là mật khẩu sai. Phải kiểm chứng kết quả thay thế ở lần thử thật, không suy ra xác thực thành công từ binding có mặt. Nếu NAS từ chối hoặc yêu cầu MFA, dừng và chẩn đoán mã lỗi trước khi thử lại. 32 kiểm thử backend đạt; phần login/logout vẫn dùng mock.

## Lần kiểm tra với secret đã được cấp

Ngày 27/10/2026: metadata xác nhận cả hai secret có saved binding, không có lỗi binding được báo. Đã gọi một lần đăng nhập bằng secret qua HTTPS đúng NAS SITE; DSM trả `success: false`, mã Auth `400`. Theo DSM Login Web API Guide chính thức, mã 400 là “No such account or incorrect password”. Chưa tạo được phiên xác thực; không gọi logout và không retry tự động. Không lưu tài khoản, mật khẩu, SID, OTP hoặc giá trị binding vào báo cáo.

Cần đối chiếu lại tài khoản DSM chính xác và cập nhật secret nếu cần. Binding có mặt không tự chứng minh việc thay thế proxy hoặc credential tới NAS đã đúng; không kết luận lỗi người dùng chỉ từ mã 400. Nếu cùng thông tin đăng nhập được trên DSM nhưng API tiếp tục trả 400, phải kiểm tra cơ chế truyền secret qua proxy trước khi thử thêm, thay vì lặp login và tăng nguy cơ auto-block. Mã 400 không phải mã yêu cầu OTP (403/406).

## Kiểm chứng đường truyền secret tiếp theo

Theo yêu cầu thử lại: một lần với form-urlencoded tiếp tục trả Auth `400`. Kiểm tra chỉ metadata cho thấy cả hai binding bị thay đổi bởi form URL-encoding; không in giá trị. Đã bổ sung chế độ multipart giữ nguyên placeholder, 33 kiểm thử backend đạt. Một lần kiểm chứng có kiểm soát với multipart nhận mã DSM `101` (invalid parameter theo mã chung). Không xác thực thành công, không logout vì chưa có SID và đã dừng. Chưa xác định liệu multipart bị DSM từ chối hay proxy thay thế làm thay đổi cấu trúc tham số; không kết luận mật khẩu sai hoặc coi multipart là bản sửa đã hoạt động. Cần kiểm chứng giao thức đóng gói được cả DSM và proxy hỗ trợ trước lần đăng nhập kế tiếp; không đưa password/SID vào URL và không retry mù.

## Kiểm tra qua Chromium theo yêu cầu người dùng

Đã khởi chạy Chromium/Playwright và điều hướng đến trang DSM HTTPS, không bỏ qua TLS. Trình duyệt chặn với `net::ERR_CERT_AUTHORITY_INVALID` trước khi tải form. Đã thử đồng bộ CA proxy có sẵn trong truststore hệ thống sang NSS và dùng proxy môi trường rõ ràng; lỗi vẫn còn. Chưa xác minh CA được Chromium thực sự sử dụng; không tuyên bố đã khắc phục truststore. Không nhập secret, không gửi login qua trình duyệt, không thay cấu hình NAS hoặc tắt TLS. Cần xử lý trust chain của Chromium trong môi trường GPT trước khi tiếp tục đường đăng nhập UI. Kết quả HTTPS của HTTPX trước đó không chứng minh truststore Chromium giống HTTPX.

### Cập nhật đường trình duyệt

Trong phiên Chromium được thực thi với quyền phù hợp sau đồng bộ trust, trang DSM đã tải với origin đúng và tiêu đề `nas-site - Synology NAS`, có trường Username; không tắt xác minh TLS. Các lỗi CA trước đó là kết quả lịch sử, không đại diện toàn bộ lần thử sau. Đã thử luồng giao diện dùng hai binding, nhưng automation kết thúc bằng TimeoutError trước khi xác nhận kết quả đăng nhập. Chưa có bằng chứng phiên xác thực thành công; context đã đóng và chưa đọc cấu hình NAS. Không coi việc đóng browser là bằng chứng logout. Không in giá trị binding, SID hoặc ảnh sau khi điền thông tin. Chưa xác định timeout ở bước UI nào; cần instrumentation theo bước trước lần kiểm chứng tiếp theo, không lặp đăng nhập mù.

## Xác định nguyên nhân đường trình duyệt

Theo yêu cầu thử lại, đã dùng nút `[syno-id="account-panel-next-btn"]` và trường password hiển thị thay vì chờ hidden input có name=password. Đã chuyển sang màn hình mật khẩu, gửi một lần Auth qua UI, DSM trả mã 400, chưa có OTP hoặc phiên thành công.

Sau đó thực hiện các phép kiểm tra chặn POST trước mạng, không login thêm. Phép kiểm tra đầu chặn cả bootstrap nên không đủ kết luận. Phép kiểm tra cuối chỉ cho phép bootstrap công khai `SYNO.API.Encryption`, rồi chặn request `SYNO.API.Auth`. Metadata xác nhận request Auth có `__cIpHeRtExT`, `ik_message`, `client`, `fid`; không có account/passwd rõ và không còn binding account/password nguyên dạng hoặc URL-encoded. Không in giá trị ciphertext hoặc secret.

Kết luận giới hạn: UI mã hóa ở client trước khi HTTPS request đi qua proxy. Với secret được proxy thay thế từ placeholder ở tầng HTTP, mã hóa placeholder làm mất điểm thay thế; không thể dùng phương pháp điền proxy binding vào UI này để chứng minh mật khẩu người dùng sai. Không tắt mã hóa DSM hoặc TLS để khắc phục. Cần cơ chế nhập trực tiếp bảo mật vào browser hoặc đường API có cơ chế truyền secret tương thích; chưa có cơ chế browser nhập trực tiếp được chia sẻ trong phiên hiện tại. Việc một phiên GPT khác đăng nhập được không chứng minh cùng cơ chế credential ở đây. Dừng thử đăng nhập thêm; chưa xem/thay đổi cấu hình NAS.
