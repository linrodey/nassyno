# Kết nối NAS — hướng Internet đã thống nhất

Trạng thái: nền tảng kiểm tra kết nối đã triển khai; chưa có NAS thật để xác minh. Prototype và hai tài liệu đầu đã được duyệt. Các lỗi chính tả được xử lý sau theo yêu cầu người dùng.

## Phương án chính

Trình duyệt người quản trị → HTTPS của ứng dụng trên máy chủ riêng → HTTPS DSM của từng NAS qua Internet. Dùng hostname riêng cho mỗi NAS, chứng chỉ khớp hostname và có chuỗi tin cậy hợp lệ. Cổng mặc định DSM HTTPS là TCP 5001; có thể dùng cổng tùy chỉnh hoặc reverse proxy HTTPS 443. Endpoint khai báo là origin, ví dụ `https://nas-01.example.vn:5001`, không chứa mật khẩu hoặc đường dẫn.

IP public trực tiếp vẫn dùng được khi chứng chỉ có IP trong Subject Alternative Name. Không tắt xác minh TLS để dùng chứng chỉ sai tên. Với CA nội bộ, cài CA đáng tin cậy trên máy chủ hoặc cấu hình `ca_file` cho từng NAS.

Nếu dùng NAT, cấu hình chuyển tiếp cổng HTTPS đích phù hợp. Nếu ISP dùng CGNAT thì NAT trên router không đủ: cần IP public có thể nhận kết nối hoặc tuyến VPN được quản lý. NAT/firewall/reverse proxy phải được kiểm tra riêng; ứng dụng chưa thay đổi cấu hình mạng này.

## Bạn cần chuẩn bị cho một NAS thử nghiệm

1. Model và phiên bản DSM đầy đủ; NAS/thư mục thử nghiệm và khung giờ thử nghiệm.
2. Hostname public hoặc IP public, cổng DSM HTTPS; bản ghi DNS và chứng chỉ đúng tên. Chỉ gửi thông tin này, không gửi mật khẩu/OTP trong chat.
3. Máy chủ ứng dụng có IP Internet đầu ra cố định. Giới hạn cổng DSM trên firewall/router/NAS chỉ nhận từ IP này (và đường quản trị hiện có cần giữ). Không tự khóa đường quản trị khi chỉnh luật.
4. Tài khoản dịch vụ riêng, ban đầu chỉ có quyền đọc cần thiết. Quyền cụ thể/MFA và khả năng API phải kiểm chứng; không mặc định cấp toàn quyền admin. Sau này cấp riêng quyền ghi theo chức năng đã duyệt.
5. Thông tin tài khoản được nhập qua cơ chế bí mật khi bước đăng nhập DSM hoàn tất; không đặt trong Git, URL, email hoặc chat. Nền tảng hiện tại chưa nhận mật khẩu NAS.

Không cần mở TCP 22 (SSH), 445 (SMB), 389 (LDAP không mã hóa) ra Internet. DSM MFA không đồng nghĩa các giao thức khác cũng được bảo vệ cùng cách.

## Vai trò từng giao thức

| Giao thức | Dùng cho | Chuẩn bị lúc này |
|---|---|---|
| HTTPS DSM | Nhận diện API, đăng nhập và thao tác API được hỗ trợ | Có; ưu tiên đầu tiên |
| SNMPv3 authPriv | Chỉ số CPU/mạng/storage/SMART được MIB/model công bố; có thể qua Zabbix | Đánh giá tiếp; không tự bật hoặc mở UDP 161 công khai |
| SSH | Chẩn đoán đặc biệt nếu có nhu cầu và được duyệt riêng | Không cần bật cho phiên bản đầu |
| LDAPS/StartTLS | Backend kết nối nguồn LDAP | Chuẩn bị sau; ưu tiên tuyến nội bộ/VPN đến directory |
| HTTPS Portal Office | Đọc User/Group theo API và quyền riêng | Cần tài liệu endpoint/schema/xác thực, không gửi key qua chat |

Một số chỉ số ổ đĩa có thể có qua SNMP nhưng không thể hứa tất cả SMART/SSD/RAID đều được cung cấp. Nếu dùng Zabbix/Prometheus, ưu tiên collector nằm gần NAS để hạn chế cổng Internet. Không giả định QuickConnect thay thế được endpoint API DSM trực tiếp.

## Khả năng đã triển khai

- Inventory chỉ do người vận hành sửa ở máy chủ; trình duyệt chỉ chọn device ID, không đưa URL tùy ý vào probe.
- Bảo vệ API bằng khóa quản trị ứng dụng (Bearer token), so sánh constant-time; đây là cơ chế bootstrap một quản trị viên, chưa phải SSO/RBAC sản phẩm.
- Probe GET `/webapi/query.cgi` với `SYNO.API.Info`, query `SYNO.API.Auth,SYNO.FileStation.Info`; không đăng nhập và không gửi lệnh ghi.
- Xác minh TLS, timeout, tối đa 4 probe đồng thời, giới hạn kích thước phản hồi và không theo redirect. Lỗi trả về không chứa response/credential chi tiết.
- Phân biệt API được công bố với API đã có quyền dùng. Health của ứng dụng không đại diện sức khỏe NAS.

Chưa có: đăng nhập/logout DSM, MFA, vault lưu credential, SSO/RBAC, audit bền vững, PostgreSQL/worker, collector metrics hoặc thao tác NAS thật. Không công bố máy chủ phát triển trực tiếp ra Internet. Trước triển khai production cần reverse proxy HTTPS, xác thực đầy đủ, rate limit, egress policy theo NAS và giám sát/audit.

Endpoint là cấu hình tin cậy của operator. Chặn IP literal loopback/link-local không thay thế firewall đầu ra: cần kiểm soát cả DNS và đích kết nối tại mạng để chống DNS rebinding/SSRF, đặc biệt nếu sau này cho nhập endpoint qua UI. Hiện chưa có API thêm/sửa endpoint từ trình duyệt.

## Nguồn và mức xác minh

Cơ chế API discovery được xây theo giao diện `SYNO.API.Info` đã biết, có kiểm thử response giả lập. Tài liệu chính thức cần đối chiếu tại Synology Developer Center: https://www.synology.com/en-global/support/developer#tool . Lần tải DSM Login Web API Guide từ `global.download.synology.com` trong môi trường này bị proxy từ chối (403); chưa xác minh được bản tài liệu mới nhất. Không dùng kết quả mock để khẳng định tương thích DSM thực tế.
