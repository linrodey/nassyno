# Bước 1 — Đặc tả để duyệt

Trạng thái: bản đề xuất, chờ duyệt trước khi triển khai backend. Ngày: 27/10/2026 (GMT+7).

## Mục tiêu và giới hạn

Quản trị khoảng 10–15 NAS, có thể mở rộng, ưu tiên DSM 7.x. Ứng dụng chạy trên máy chủ riêng. Các repo quản trị Firewall, Switch, Wi-Fi tương lai được triển khai độc lập. Zabbix/Prometheus là nguồn giám sát có thể tích hợp, không phải điều kiện bắt buộc của phiên bản đầu.

Phiên bản đầu có giá trị sử dụng: đăng nhập, phân quyền theo địa điểm/NAS, quản lý kết nối, tổng quan, kiểm kê lưu trữ, duyệt metadata File Station, User/Group chỉ đọc và nhật ký. Các thao tác ghi được mở ở các bước sau khi kiểm chứng khả năng DSM và được duyệt.

Không tự nâng DSM, không mặc định bật SSH, không dùng API ẩn hoặc bỏ qua TLS. Chưa thực hiện thao tác thật lên thiết bị. Chưa xác minh model, phiên bản DSM, API, LDAP hoặc Portal Office thực tế. Không coi chức năng xuất hiện trong prototype là bằng chứng DSM hỗ trợ.

## Vai trò và phạm vi

| Vai trò | Quyền dự kiến |
|---|---|
| Người xem | Xem giám sát trong địa điểm/NAS được cấp |
| Quản trị danh tính | Quản lý tài khoản, nhóm và kế hoạch đồng bộ trong phạm vi được cấp |
| Quản trị dữ liệu | Duyệt metadata, quản lý ACL theo thư mục được cấp |
| Quản trị thiết bị | Kết nối NAS, chẩn đoán và thao tác thiết bị được cho phép |
| Người duyệt | Duyệt kế hoạch thay đổi thuộc phạm vi được cấp |
| Quản trị ứng dụng | Quản lý người dùng ứng dụng và cấu hình; quyền thao tác NAS vẫn kiểm tra riêng |

Backend kiểm tra quyền từng yêu cầu, từng NAS và từng đối tượng. Không dựa vào việc ẩn nút trên giao diện. Tác vụ nhạy cảm có thể yêu cầu người duyệt khác người đề xuất theo chính sách.

## Chức năng và bằng chứng cần có

| Phân hệ | Phạm vi | Cần xác minh trên NAS thử nghiệm |
|---|---|---|
| Kết nối NAS | Địa chỉ HTTPS, TLS, model, DSM, địa điểm, kiểm tra năng lực | Đăng nhập, hết phiên, MFA, quyền tối thiểu, logout |
| Giám sát | CPU, RAM, mạng, uptime, trạng thái cập nhật | Nguồn API/collector được hỗ trợ và đơn vị đo |
| Kết nối/dịch vụ | Phiên người dùng, IP, giao thức, ngắt phiên; cổng cấu hình | Giao thức nào cung cấp dữ liệu và cho phép ngắt phiên |
| File Station | Duyệt/tìm metadata, phân trang, tên Unicode, quyền xem | API File Station chính thức, đường dẫn và quyền thực tế |
| Danh tính | User/Group thủ công, LDAP, API Portal Office | Schema, định danh ổn định, phân trang, quyền và phạm vi ghi |
| ACL | Quyền share, Windows ACL, kế thừa, Allow/Deny, nhóm | Khả năng đọc/ghi và đối chiếu truy cập SMB thực tế |
| Firewall | Đọc luật; đề xuất cho phép/chặn IP; xem trước | API được hỗ trợ, thứ tự luật, IPv4/IPv6, khả năng khôi phục |
| Lưu trữ | HDD/SSD, Pool/RAID, Volume, SSD Cache, LUN/Target | API/collector hỗ trợ theo model, DSM và package |

Mỗi chức năng có trạng thái: chưa kiểm tra / được hỗ trợ / chỉ đọc / không được hỗ trợ. Khi không được hỗ trợ, giao diện giải thích rõ và không cho thực hiện. Cổng được cấu hình không đồng nghĩa cổng lắng nghe hoặc truy cập được từ ngoài.

## Lưu trữ vật lý và logic

- Ổ vật lý: khay (kể cả enclosure mở rộng), HDD/SSD, model, serial, firmware, dung lượng byte, nhiệt độ, sức khỏe, tuổi thọ SSD nếu có.
- S.M.A.R.T.: khả năng hỗ trợ, kết quả/lần kiểm tra gần nhất, chỉ số được công bố; phân biệt chưa có dữ liệu và sức khỏe tốt. Lên lịch kiểm tra nhanh/mở rộng chỉ sau khi xác minh hỗ trợ và ảnh hưởng.
- Pool: RAID/SHR, ổ thành viên, Hot Spare, tổng khả dụng sau RAID, degraded/rebuild/scrub và tiến độ khi có dữ liệu.
- Volume: Pool chứa volume, Btrfs/ext4, capacity/used/free, trạng thái. Cache: ổ thành viên, chế độ và sức khỏe. LUN/Target: quan hệ, provisioning và dung lượng nếu có SAN Manager.
- Hiển thị dung lượng vật lý riêng với dung lượng pool/volume, không cộng các lớp. Tổng volume toàn hệ thống chỉ tính đối tượng có dữ liệu hợp lệ; báo số NAS thiếu dữ liệu. Chuẩn lưu byte, hiển thị TiB/GiB; phân biệt cấp phát với sử dụng thực tế của thin provisioning.
- Không giả định mọi Pool đều là một volume hay mọi thiết bị đều có S.M.A.R.T./Cache/LUN. Quan hệ lưu trữ có trạng thái chưa xác định khi nguồn thiếu thông tin.
- Tạo/xóa Pool, khởi tạo ổ, thay RAID và sửa chữa/mở rộng thuộc giai đoạn riêng, ngoài phiên bản đầu.

## Danh tính và đồng bộ

Nguồn: thủ công, LDAP và Portal Office. Dùng khóa `(source_id, external_id)` ổn định, không dùng tên hiển thị/email làm khóa duy nhất. Tài khoản DSM cục bộ và tài khoản LDAP/AD là các loại riêng; không tự tạo bản sao tài khoản miền trên mỗi NAS.

Mặc định đồng bộ một chiều, có dry-run. Quy tắc ánh xạ nhóm, thuộc tính được nguồn nào sở hữu, NAS đích và xử lý xung đột phải cấu hình rõ. Trùng tên khác định danh cần xử lý thủ công. Nguồn mất kết nối không được suy ra mọi tài khoản đã bị xóa. Mặc định không xóa tài khoản khi biến mất khỏi nguồn; đưa vào danh sách xem xét. Không đồng bộ mật khẩu từ LDAP/Portal.

Cần tài liệu Portal Office: endpoint, phương thức xác thực, định danh, schema User/Group, phân trang, giới hạn tốc độ và cơ chế tài khoản ngừng hoạt động. Chỉ yêu cầu thông tin xác thực qua cơ chế bí mật, không qua chat/Git.

## ACL và thao tác thay đổi

Hiển thị quyền share, ACL trực tiếp/kế thừa, Allow/Deny và nhóm. Không kết luận quyền hiệu lực chỉ từ một ACE. Khả năng giải thích quyền phải được đối chiếu với SMB; trường hợp chưa đủ dữ liệu hiển thị chưa xác định.

Luồng thay đổi: chọn đối tượng → lấy trạng thái hiện tại → tạo bản trước/sau và phạm vi ảnh hưởng → duyệt → kiểm tra lại trạng thái/quyền → thực thi → đọc lại xác minh → lưu kết quả. Nếu trạng thái đã đổi, yêu cầu tính lại kế hoạch. Không áp quyền đệ quy mặc định. Rollback chỉ được đánh dấu khả dụng khi đã kiểm chứng; tác vụ một phần phải ghi rõ đối tượng thành công/thất bại.

Firewall cần kiểm tra đường quản trị và thứ tự luật. Nếu không có đường khôi phục đã kiểm chứng, khóa thao tác có thể làm mất kết nối quản trị. Không hứa rollback tự động khi kết nối đã mất.

## Kiến trúc đề xuất

React + TypeScript; FastAPI; PostgreSQL cho dữ liệu nghiệp vụ; worker riêng và Redis cho hàng đợi khi mở tác vụ nền. Docker Compose trên máy chủ riêng ở giai đoạn đầu. Chưa chốt sizing cho production trước khi biết tần suất thu thập và khối lượng dữ liệu.

Trình duyệt → backend → adapter DSM/LDAP/Portal. Collector đọc trực tiếp hoặc adapter Zabbix/Prometheus cung cấp metrics. Mỗi chỉ số có source, observed_at, collected_at, unit, quality. Cấu hình một nguồn chính cho mỗi chỉ số, không âm thầm trộn các nguồn. Đề xuất thăm dò chỉ số 60 giây, inventory 15 phút; điều chỉnh sau đo tải, tránh tác vụ chồng nhau trên cùng NAS. Không crawl toàn bộ file system định kỳ.

Các ứng dụng sở hữu database riêng, tích hợp qua API `/api/v1` và sự kiện có schema phiên bản. Chuẩn bị định danh site/device chung và SSO OIDC; chưa xây cổng quản trị hoặc dịch vụ dùng chung thành điều kiện cho phiên bản đầu. Khi cần lịch sử metrics dài hạn, dùng backend time-series phù hợp thay vì lưu mọi mẫu vào bảng nghiệp vụ.

## Mô hình dữ liệu và API dự kiến

Thực thể: Site, NasDevice, Capability, CredentialReference, Observation, Disk, StoragePool, PoolDisk, Volume, Cache, Lun, Target, IdentitySource, ExternalIdentity, NasAccountMapping, GroupMembership, AclSnapshot, ChangePlan, Approval, Job, JobItem, AuditEvent.

Dữ liệu luôn gắn device_id/source_id; đường dẫn file phải thuộc root được phép. NAS URL phải được kiểm soát đích để tránh SSRF; thay đổi endpoint cần kiểm tra lại. Không lưu mật khẩu hoặc phiên DSM trong bảng metadata/log.

API dự kiến: `/devices`, `/devices/{id}/capabilities`, `/devices/{id}/storage`, `/devices/{id}/files`, `/identity-sources`, `/sync-plans`, `/change-plans`, `/jobs`, `/audit-events`. Lệnh ghi dùng idempotency key, kiểm soát đồng thời, timeout và đối chiếu kết quả trước khi retry. Không retry mù thao tác tạo tài khoản hoặc cập nhật ACL.

## Bảo mật và vận hành

TLS được xác minh; hỗ trợ CA nội bộ qua trust store. Bí mật được mã hóa với khóa tách khỏi DB và Git; quản lý phiên NAS phía server, che dữ liệu nhạy cảm trong lỗi/log. LDAP dùng LDAPS hoặc StartTLS đã xác minh. SSO/MFA cho ứng dụng khi tích hợp được IdP; không giả định MFA ứng dụng thay thế bảo vệ SMB/WebDAV.

Audit ghi người thực hiện/duyệt, phạm vi, thời gian, trước/sau đã lọc bí mật và kết quả. Tách quyền sửa dữ liệu nghiệp vụ khỏi quyền quản lý audit; chính sách lưu giữ và xuất log sẽ được chốt trước production. Sao lưu DB và cấu hình, kiểm thử phục hồi; không đưa khóa giải mã chung với bản backup không được bảo vệ.

## Giao diện

Menu: Tổng quan, Lưu trữ, File Station, Danh tính, Phân quyền, Kết nối & Firewall, Nhật ký. Bộ lọc địa điểm/NAS; phân biệt online, lỗi xác thực, mất kết nối và dữ liệu cũ. Chi tiết lưu trữ gồm sơ đồ khay, các lớp dung lượng, bảng ổ và Pool/Volume.

Prototype hiện minh họa luồng chọn NAS, xem lưu trữ, duyệt file metadata, lọc danh tính, xem trước thay đổi ACL/IP và nhật ký. Chỉ dùng dữ liệu giả, không đăng nhập thật, chưa triển khai đầy đủ các màn hình hoặc cơ chế bảo mật production.

## Cần bổ sung trước kết nối thực tế

Danh sách model/DSM/địa điểm; NAS và thư mục thử nghiệm; tuyến mạng từ máy chủ; CA nội bộ; cơ chế tài khoản dịch vụ/MFA; schema LDAP/Portal; IdP nếu có; Zabbix/Prometheus hiện có hay dự kiến. Những thông tin này không chặn việc duyệt thiết kế bằng dữ liệu giả.
