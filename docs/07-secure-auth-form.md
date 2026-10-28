# Form kiểm tra đăng nhập NAS

Đã tạo form web, không cần Python trên máy người dùng. Backend vẫn cần nơi chạy. Khung chat hiện không cung cấp public web hosting/port preview để người dùng nhập credential vào một ứng dụng sống; không dùng HTML tải về thay cho một backend đáng tin cậy.

## Gói Windows dùng localhost

Yêu cầu Windows 10/11 hỗ trợ Docker Desktop chạy Linux containers, Docker Compose và Internet để tải base image/dependencies. Python nằm trong container, không cài trên Windows. Docker Desktop không phải lựa chọn mặc định cho Windows Server; nếu máy là Windows Server, cần phương án Linux VM/container host phù hợp trước khi dùng gói này.

1. Cài/mở Docker Desktop từ nguồn chính thức nếu chưa có.
2. Giải nén toàn bộ gói, giữ nguyên cấu trúc. Chạy `deploy/windows/Mo-Form.cmd`.
3. Lần đầu, script yêu cầu tạo khóa truy cập ứng dụng ít nhất 32 ký tự. Đây không phải mật khẩu NAS. Nhớ khóa để nhập vào form mở trong trình duyệt; script không in/copy khóa ra clipboard.
4. Script dựng container và mở trình duyệt trên localhost. Nhập khóa ứng dụng → tải danh sách → NAS SITE → Đăng nhập thử → kiểm tra đúng endpoint → nhập tài khoản, mật khẩu và OTP nếu có → xác nhận → kiểm tra đăng nhập và logout.
5. Chỉ gửi lại kết quả/mã lỗi, không gửi credential hoặc SID. Nếu logout không xác nhận, kiểm tra phiên trong DSM trước khi thử tiếp.
6. Dừng bằng `docker compose down` trong thư mục `deploy/windows`. Khóa ứng dụng nằm ở `runtime/app-token`, giới hạn ACL cho người Windows hiện tại; đây không phải NAS credential. Xóa file này khi đã dừng ứng dụng để đặt lại khóa.

`Mo-Form.cmd` dùng ExecutionPolicy Bypass cho đúng tiến trình PowerShell chạy script cục bộ, không sửa execution policy toàn hệ thống. Người vận hành nên đọc script trước khi chạy; bản Windows chưa được ký số và chưa được chạy trên máy Windows thực tế.

## Bảo vệ đã có

- Cổng container chỉ bind `127.0.0.1:8080`, không công bố ra LAN/Internet. HTTP chỉ được dùng cho loopback cục bộ; browser → NAS vẫn là backend HTTPS với TLS verification.
- Chế độ Docker local phải bật rõ và chỉ chấp nhận đúng origin `http://127.0.0.1:8080`. Không được đổi port bind thành `0.0.0.0` hoặc đưa chế độ này sau public reverse proxy.
- Khi triển khai nhiều người dùng, bắt buộc hostname HTTPS được khai báo trong `NAS_MANAGER_CONSOLE_ORIGINS`, cấu hình trusted proxy, xác thực/RBAC và bảo vệ triển khai đầy đủ. Không dùng bootstrap local như SSO production.
- Bearer key ứng dụng, kiểm tra same-origin, không CORS rộng; không để NAS password/SID trong URL; POST body được giới hạn 8 KiB và lỗi nhập liệu không echo input.
- Ba lần kiểm tra trên mỗi NAS trong 15 phút, một lần đang chạy trên mỗi NAS; giới hạn nằm trong bộ nhớ một worker và bị reset khi restart. Không thay thế bảo vệ đăng nhập của DSM hoặc rate limit triển khai nhiều worker.
- Password/OTP được xóa khỏi trường nhập khi gửi, đóng form hoặc rời trang. Không localStorage/sessionStorage/cookie lưu credential; form không có chức năng ghi mật khẩu NAS vào DB/file/log. SID/SynoToken chỉ dùng trên backend và không trả cho trình duyệt.
- Không bật trusted device, không bypass MFA, không retry tự động. Nếu mất kết nối sau gửi login, trạng thái có thể chưa xác định; không hứa logout khi NAS không phản hồi.
- Kiểm tra tiếp tục cleanup trong task backend nếu browser request bị cancel. Khi process bị kill/máy mất điện, phiên có thể còn tồn tại trên DSM tới lúc timeout hoặc được quản trị viên đóng.

Không thể cam kết không có bí mật trong RAM: xử lý login cần dữ liệu rõ trong bộ nhớ trình duyệt/backend trong thời gian ngắn. Python/JavaScript không cung cấp đảm bảo zeroization; browser extensions, password manager, malware, OS crash dump, proxy/APM logging và người quản trị máy chủ nằm ngoài các bảo vệ của form. Không dùng máy/chủ dịch vụ không đáng tin, không bật ghi request body trên reverse proxy/APM.

## Kiểm thử thực tế

- 29 kiểm thử backend đạt: xác thực API, HTTP không an toàn, origin khác/thiếu, payload lỗi không echo, kích thước body, giới hạn lần thử, cấu hình local và lỗi upstream được lọc.
- Chromium: dùng credential giả, nhập/gửi form, xóa trường mật khẩu/OTP, không retry, không ghi browser storage, cảnh báo logout chưa xác nhận, xóa khóa và mobile layout.
- Đã build Docker image và khởi chạy Linux container nonroot/read-only, xác minh secret mount, health, inventory và bảo vệ route auth; không gửi credential NAS thật.
- Build trong cloud cần CA bundle proxy của môi trường qua BuildKit secret `build_ca`; không tắt TLS và không đóng gói CA của cloud vào image. Nếu Windows có HTTPS inspection, cần cấu hình CA tổ chức đáng tin cậy riêng; không bỏ qua kiểm tra chứng chỉ.
- Chưa kiểm thử script PowerShell/ACL trên Windows thực tế, chưa đăng nhập NAS thật và chưa đánh giá bảo mật production toàn diện.
