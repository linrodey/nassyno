# Ma trận bằng chứng — Bước 2 đang thực hiện

Không có credential/cookie nào được chuyển giữa các phiên GPT. Trạng thái dưới đây tổng hợp các phép thử đã ghi nhận, không khẳng định sức khỏe kết nối liên tục.

| Chức năng | Bằng chứng hiện có | Chưa được chứng minh | Điều kiện tiếp theo |
|---|---|---|---|
| HTTPS NAS SITE | TLS và discovery đã thành công bằng HTTPX; Chromium tải được trang DSM | Kết nối ổn định trong môi trường triển khai cuối | Kiểm tra lại từ máy chủ thử nghiệm |
| Auth API | Discovery công bố phiên bản 1–7; đã đọc tài liệu chính thức | Login/logout thành công với credential thật ở backend hiện tại | Đường truyền credential tương thích proxy hoặc backend tin cậy |
| File Station | Discovery công bố Info 1–2 | Liệt kê metadata/quyền qua backend | Xác thực thành công, thư mục thử nghiệm được chỉ định |
| CPU/RAM/mạng/uptime | Prototype giả lập | Thu thập chỉ số thật và đơn vị | Báo cáo UI để thiết kế mapping; sau đó kiểm chứng adapter |
| HDD/SSD/SMART | Đặc tả/mẫu giao diện | Model/khay/SMART hiện tại và API/MIB | Khảo sát UI chỉ đọc, xác minh nguồn được hỗ trợ |
| Pool/Volume/RAID/Cache/LUN | Mô hình dữ liệu đề xuất | Quan hệ và capacity thực tế | Khảo sát theo lớp, không cộng trùng; kiểm chứng adapter |
| User/Group/LDAP | Mẫu ba nguồn | Cấu hình nguồn/nhóm và quyền truy cập | Báo cáo đã lọc, schema LDAP/Portal, sandbox |
| ACL | Luồng xem trước dùng mock | Quyền hiệu lực và khả năng đọc/ghi DSM | Thư mục thử nghiệm, đọc trước; ghi chưa được mở |
| Firewall/phiên | Giao diện minh họa | API hỗ trợ và đường khôi phục | Khảo sát UI; thao tác ghi tiếp tục khóa |
| QuickConnect | Yêu cầu đã ghi nhận | API/session/relay tương thích | Khảo sát dịch vụ, tài liệu chính thức, thử riêng |
| Backend safety | 33 kiểm thử trước khảo sát đã đạt, form Chromium và container smoke đã đạt | SSO/RBAC, audit bền vững, secret vault, production hardening | Thiết kế và nghiệm thu triển khai riêng |

Báo cáo từ phiên GPT Công việc luôn có provenance `operator_ui_report`: có thể chứng minh người vận hành đã quan sát UI nếu được rà soát, không nâng trạng thái thành backend/API đã kiểm chứng. Template mặc định `not_checked`, không tự điền thông tin từ baseline.

Không thử tạo tài khoản, ACL, firewall hoặc thay đổi storage trước khi có kiểm chứng backend và duyệt bước tương ứng. Những thử nghiệm bằng tài khoản admin trước đây chỉ là đăng nhập thất bại, không chứng minh quyền ứng dụng.
