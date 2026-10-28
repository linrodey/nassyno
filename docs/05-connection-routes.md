# Các đường kết nối đã thống nhất

Ngày 27/10/2026 (GMT+7). Người dùng cho phép kiểm tra chỉ đọc `https://nassite.hbcg.vn:5001`. Chưa có tài khoản hoặc bí mật NAS trong ứng dụng.

| Đường kết nối | Endpoint | Trạng thái |
|---|---|---|
| HTTPS public | Hostname hoặc IP public + port | Backend đã triển khai; lần thử mới nhất xác minh TLS và API discovery thành công |
| HTTPS qua VPN | Hostname/IP nội bộ + port | Dùng cùng adapter HTTPS; cần tuyến mạng và DNS/VPN của môi trường thực thi được cấu hình |
| HTTPS LAN | Hostname/IP nội bộ + port | Dùng cùng adapter; cần máy chủ có tuyến mạng tới NAS |
| QuickConnect | ID/URL QuickConnect được người dùng cung cấp | Nằm trong phạm vi thiết kế; chưa triển khai connector, chưa xác minh API hoặc relay |

`route` là metadata chọn đường vận hành (`public`, `vpn`, `lan`), không tự tạo VPN, mở NAT hoặc cấu hình firewall. Cấu hình mẫu NAS SITE ở `config.nassite.example.json`; không thay đổi cấu hình NAS hoặc tự đăng nhập khi tải inventory.

HTTPS bằng IP chỉ hợp lệ khi chứng chỉ có IP tương ứng; qua VPN cũng phải xác minh TLS. Hostname với split DNS có thể giữ nguyên tên chứng chỉ khi đi đường nội bộ. Khi đổi endpoint/tuyến, phải kiểm tra lại và không tự mang phiên xác thực sang hostname khác. Phiên bản hiện tại chỉ có một endpoint đang hoạt động cho mỗi NAS, chưa có failover nhiều endpoint tự động.

## QuickConnect

Chấp nhận đây là yêu cầu sản phẩm. Chưa thể cam kết mọi API đều hoạt động qua QuickConnect chỉ vì trang DSM truy cập được. Trước khi mở chế độ này cần:

1. ID hoặc URL QuickConnect của NAS thử nghiệm (không phải tài khoản/mật khẩu).
2. Đối chiếu tài liệu Synology chính thức về dịch vụ và phạm vi truy cập; không tự dùng API discovery nội bộ/không công bố của QuickConnect.
3. Kiểm chứng backend → API DSM, đăng nhập/MFA/logout, File Station, timeout, đường relay và miền đích/TLS.
4. Chỉ cho chuyển hướng đến đích đã được kiểm chứng và cho phép, không bỏ chính sách chống redirect của connector HTTPS hiện tại.
5. Nếu không có giao diện tích hợp được hỗ trợ cho chức năng yêu cầu, báo giới hạn cụ thể; tiếp tục dùng HTTPS public/VPN và có thể dùng QuickConnect như liên kết mở DSM cho người quản trị.

Không yêu cầu mở rộng wildcard cho toàn bộ miền QuickConnect trước khi xác định đích thực tế.

## Kết quả phép thử NAS SITE

- Probe API discovery thất bại với `network_or_proxy_error`.
- Chẩn đoán hẹp xác nhận proxy từ chối CONNECT (403). Đây là lỗi trên đường đi của môi trường cloud, không phải bằng chứng DSM trả 403.
- Chưa xác minh chứng chỉ NAS, phiên bản DSM, khả năng API hoặc quyền tài khoản; không thử login và không thay đổi NAS.
- Đã lưu bản nháp thêm ba hostname: `nassite.hbcg.vn`, `www.synology.com`, `global.download.synology.com`. Giữ nguyên preset package-manager và không mở Internet toàn bộ. Hai hostname Synology phục vụ đối chiếu tài liệu API/QuickConnect.
- Công cụ xác nhận bản nháp đã lưu và cần publish. Lưu draft không áp dụng runtime. Người dùng cần xem xét/lưu trong environment settings rồi Publish; sau đó chạy lại probe và đọc tài liệu. Nếu vẫn lỗi, kiểm tra hạn chế cổng 5001, policy proxy, firewall hoặc tuyến NAS dựa trên lỗi mới.

Skill quản trị NAS yêu cầu đọc baseline; SKILL.md đã đọc được nhưng hai tài nguyên `references/nas-site-baseline.md` và `references/operations.md` không tải được qua công cụ skill. Không suy diễn hiện trạng từ hồ sơ cũ; chưa thực hiện khảo sát cấu hình hoặc thao tác quản trị DSM. Cần khôi phục quyền đọc các tài nguyên này trước khảo sát cấu hình NAS chuyên sâu.

## Cập nhật phép thử tiếp theo

CLI chẩn đoán đã nhận discovery hợp lệ từ NAS SITE, TLS được xác minh, Auth 1–7 và FileStation.Info 1–2 được công bố. Không login hoặc thay đổi cấu hình. Tài liệu DSM Login Web API Guide cũng tải được từ nguồn chính thức. Các lỗi proxy nêu trên là lịch sử phép thử, không còn là blocker của lần kết nối mới. Xem docs/06-api-troubleshooting.md cho trạng thái và bước xác thực tiếp theo.
