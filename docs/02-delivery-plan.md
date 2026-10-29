# Kế hoạch thực hiện và kiểm thử

Mỗi bước gửi kết quả để người dùng duyệt, chỉ chuyển bước sau khi được duyệt. Các thông số trong đặc tả là đề xuất đến khi có bằng chứng thực tế.

| Bước | Bàn giao | Điều kiện nghiệm thu |
|---|---|---|
| 1. Đặc tả và thiết kế | Đặc tả, prototype dữ liệu giả, danh sách khả năng cần kiểm chứng | Duyệt phạm vi, giao diện, luồng thay đổi và các giới hạn |
| 2. Kiểm chứng DSM và nền tảng | Ma trận API theo NAS mẫu, backend/frontend, đăng nhập và kết nối | TLS đúng; lỗi xác thực/timeout rõ; kiểm tra quyền xuyên NAS; không lộ bí mật |
| 3. Chức năng chỉ đọc | Dashboard, storage, file metadata, User/Group, audit | Đối chiếu DSM; phân trang/Unicode; thiếu dữ liệu không hiện khỏe; không cộng trùng capacity |
| 4. Danh tính | Tạo User/Group, adapter LDAP/Portal, dry-run đồng bộ | Khóa ổn định; xung đột; nguồn mất kết nối; chạy lại không tạo trùng; lỗi một phần được báo |
| 5. ACL | Xem trước, duyệt và thực thi thay đổi trên dữ liệu thử nghiệm | Allow/Deny, nhóm, kế thừa; SMB thực tế; bảo toàn ngoại lệ; kiểm chứng khôi phục |
| 6. Firewall và phiên | Các chức năng đã có bằng chứng hỗ trợ | Thứ tự luật, IPv4/IPv6, đường quản trị dự phòng; quyền ngắt phiên; không thao tác production khi chưa nghiệm thu |
| 7. Tích hợp và vận hành | Zabbix/Prometheus khi cần, backup, hướng dẫn, triển khai | Nguồn/thời gian metric rõ; tải 15 NAS và tình huống mất kết nối; phục hồi backup; nghiệm thu đầu cuối |

## Nhánh triển khai File Audit & Version Control (được bổ sung 29/10/2026)

- FA-0 khảo sát read-only nguồn log/versioning và quyền qua các giao thức; không cấu hình NAS.
- FA-1 mock UI, mô hình dữ liệu, collector chỉ đọc, tra cứu sự kiện; nghiệm thu trên NAS thử nghiệm sau khi nền tảng kết nối Bước 2 hoàn tất.
- FA-2 truy vấn phiên bản và phục hồi theo phê duyệt trên dữ liệu thử nghiệm.
- FA-3 so sánh nội dung Word/Excel của hai phiên bản trong môi trường xử lý bảo mật.

Đặc tả chi tiết và backlog: [docs/12-file-audit-version-control.md](12-file-audit-version-control.md). Không thay đổi điều kiện nghiệm thu của Bước 2 hiện tại.

## Cách kiểm thử

- Unit: chuyển đổi đơn vị, tính tổng đúng lớp, ánh xạ danh tính, idempotency và trạng thái tác vụ.
- Integration: adapter với response fixtures đã lọc bí mật và NAS thử nghiệm; LDAP/Portal sandbox; phiên hết hạn và lỗi từng phần.
- End-to-end: người dùng theo từng vai trò, chọn NAS, đọc dữ liệu, lập/duyệt thay đổi, xem kết quả và audit.
- Bảo mật: vượt phạm vi NAS/thư mục, path traversal, SSRF, CSRF nếu dùng cookie, phân quyền API, rò rỉ credential/log và truy cập audit.
- Hiệu năng: dữ liệu ít nhất 15 thiết bị giả lập, NAS chậm/offline không chặn các NAS khác, kiểm tra concurrency/rate limit thực tế trước chốt production.
- Storage: không hỗ trợ SMART, thiếu dữ liệu, SSD cache, pool degraded, rebuild, nhiều volume trên một pool, thin LUN và enclosure mở rộng.

Chỉ dùng tài khoản/thư mục/thiết bị thử nghiệm đã thống nhất cho thao tác ghi. Ghi rõ passed/failed/skipped/unrun và phiên bản DSM đã kiểm chứng. Không dùng kết quả mock để khẳng định NAS thật hoạt động.

## Xác minh bản thiết kế hiện tại

Chạy `node --test prototype/model.test.cjs` và kiểm tra cú pháp JavaScript. Prototype không có backend; kiểm thử hiện tại chỉ chứng minh logic lọc dữ liệu, tổng dung lượng và giới hạn bản xem trước. Cần người dùng xem giao diện trên trình duyệt trước duyệt. Chưa thực hiện kiểm thử DSM, LDAP, Portal, tải production hoặc trình duyệt tự động.
