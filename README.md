# nassyno

Ứng dụng web quản trị nhiều NAS Synology, dự kiến triển khai trên máy chủ riêng. Đặc tả và prototype đã được duyệt; **Bước 2 — nền tảng kết nối chưa hoàn tất**.

## Trạng thái thực tế

- Đã xác minh HTTPS/TLS và API discovery NAS SITE; Auth 1–7, FileStation.Info 1–2 được công bố.
- Backend hiện tại chưa đăng nhập thành công hoặc đọc trực tiếp cấu hình NAS có xác thực; đã nhận báo cáo UI từ phiên GPT Công việc. Các phép thử login trả 400/101; giao diện DSM mã hóa đầu vào khiến proxy binding không còn điểm thay thế.
- Backend, form và adapter hiện có kiểm thử mock; prototype dùng dữ liệu giả. Không suy ra ứng dụng đã quản trị được NAS thật.
- Chưa có SSO/RBAC, audit bền vững, secret vault hoặc triển khai production. Chưa mở thao tác ghi.

## Đặc tả và bản mẫu đã duyệt

- [Đặc tả](docs/01-specification.md)
- [Kế hoạch và kiểm thử](docs/02-delivery-plan.md)
- [Prototype](prototype/index.html), [ảnh dashboard](prototype/overview-desktop.png), [lưu trữ](prototype/storage-desktop.png)

## Bàn giao và phương án kết nối

- [Phương án kết nối đã chốt và giới hạn thực tế](docs/10-connection-decision.md)
- [Tải gói khảo sát](downloads/nassyno-survey-kit.zip) — mở file trên GitHub rồi chọn Download raw.
- [Yêu cầu khảo sát dạng văn bản](survey/prompt-gpt-cong-viec.txt) — có thể đọc/copy trực tiếp, không bắt buộc tải ZIP.

## Báo cáo UI đã nhận

- [Rà soát khảo sát ngày 28/10/2026](docs/11-survey-review.md): JSON hợp lệ, 12 mục observed và 2 mục not_checked.
- Báo cáo gốc giữ ngoài Git; kết quả UI không thay thế kiểm thử NAS thật của backend.

## Công việc hiện tại

- [Gói khảo sát chỉ đọc cho phiên GPT Công việc](docs/08-readonly-survey-handoff.md)
- [Yêu cầu để chuyển sang phiên đã đăng nhập](survey/prompt-gpt-cong-viec.txt)
- [Mẫu JSON chưa có kết quả thật](survey/template.json)
- [Ma trận bằng chứng và phần chưa kiểm chứng](docs/09-evidence-matrix.md)

Phiên này không điều khiển được phiên GPT khác; người dùng chuyển yêu cầu khảo sát rồi mang báo cáo đã lọc bí mật về. Không chuyển mật khẩu, cookie, SID hoặc nội dung tài liệu doanh nghiệp.

## Kết nối và chạy thử

- [Kết nối Internet](docs/03-nas-connectivity.md), [public/VPN/QuickConnect](docs/05-connection-routes.md)
- [Khởi động nền tảng](docs/04-running-foundation.md), [nhật ký troubleshoot](docs/06-api-troubleshooting.md)
- [Form và gói Windows local tùy chọn](docs/07-secure-auth-form.md); không bắt buộc cài trên máy cá nhân.

```bash
python3 -m unittest discover -s tests -v
node --test prototype/model.test.cjs
python3 -m backend.survey_report survey/template.json
```

Không lưu credential hoặc báo cáo cấu hình thực vào Git. Công cụ kiểm tra report chỉ xác thực cấu trúc, không đảm bảo phát hiện mọi bí mật trong nội dung tự do. Các tài liệu troubleshoot giữ lịch sử; ưu tiên trạng thái mới nhất ở README và ma trận bằng chứng.
