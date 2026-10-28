# Tiếp nhận khảo sát UI ngày 28/10/2026

Đã tiếp nhận JSON và Markdown do người dùng cung cấp từ phiên GPT Công việc. JSON vượt kiểm tra schema; 12/14 mục observed, SSD Cache và ACL not_checked. Thời điểm báo cáo có timezone GMT+7. Đây là nguồn `operator_ui_report`, không phải phép kiểm tra live của backend hiện tại.

Hai báo cáo gốc nằm trong `survey/incoming/`, kết quả kiểm tra nội bộ trong `survey/results/`; các thư mục đã bị gitignore. Không đưa báo cáo cấu hình hoặc bản ánh xạ alias sang tên thật lên GitHub. Tài liệu này chỉ ghi nhận kết luận thiết kế và phạm vi bằng chứng.

## Kết luận thiết kế cần giữ

- Tách ổ vật lý, Hot Spare, Pool, Volume, Cache và LUN. Pool đã cấp hết cho Volume không đồng nghĩa Volume gần đầy; chỉ dùng số liệu đúng lớp cho cảnh báo.
- Giữ nguyên đơn vị, số làm tròn và nguồn dữ liệu UI. Không tự đổi nhãn TB thành TiB hoặc suy ra byte chính xác từ số làm tròn. Số total/used/free không nhất thiết cộng đúng tuyệt đối do độ chính xác UI.
- Tình trạng Healthy, lần self-test gần nhất và SMART attributes là các trường khác nhau. Một mẫu ổ không đại diện toàn bộ ổ; chưa có log không được hiển thị là self-test passed.
- Không thấy SSD trong bảng ổ đã tải không chứng minh mọi enclosure đều không có SSD; SSD Cache chưa khảo sát chuyên biệt.
- SAN Manager hiện diện, bảng LUN/Target không có đối tượng tại thời điểm xem: dịch vụ có thể truy cập và danh sách rỗng là hai thông tin riêng.
- Danh sách User/Group đã tải không chứng minh đã phân loại đầy đủ local/domain/LDAP. Số đối tượng có thể chọn trong tab Members không phải số thành viên nhóm.
- Không gán hai số lưu lượng chưa xác định chiều thành upload/download. Không suy ra link status từ đồ thị LAN.
- QuickConnect được bật qua UI không chứng minh API/session qua relay hoạt động. Backend vẫn ưu tiên HTTPS trực tiếp hoặc qua VPN đã chuẩn bị.
- Domain/LDAP hiển thị yêu cầu Join và SNMP chưa bật trong báo cáo: không tự bật hoặc join để có dữ liệu. Tích hợp LDAP/Portal của ứng dụng độc lập với việc NAS tham gia directory.
- ACL chưa được đọc do chưa chỉ định thư mục thử nghiệm. Không dùng baseline hoặc quyền share để suy ra quyền hiệu lực của thư mục con.

## Những việc còn chặn nghiệm thu Bước 2

1. Backend chưa đăng nhập, đọc và logout thành công trên NAS thật. Không nâng trạng thái do phiên GPT Công việc đăng nhập được.
2. Chưa có hostname HTTPS và host thử nghiệm của ứng dụng để người dùng nhập credential trực tiếp ngoài cơ chế proxy GPT.
3. Chưa chỉ định thư mục thử nghiệm để kiểm tra metadata/ACL; không tự tạo hoặc chọn thư mục nghiệp vụ.
4. Chưa kiểm chứng API cho metrics/storage/User/Group/firewall. UI quan sát được không thay thế tài liệu và request API thành công.
5. Phiên bản DSM trong báo cáo là dữ liệu người vận hành cung cấp, chưa đối chiếu tài liệu tương thích/model qua backend. Không nâng DSM hoặc sửa version theo giả định.

## Bàn giao tiếp theo

Giữ nguyên điểm duyệt theo kế hoạch: hoàn tất đường xác thực backend trước khi nghiệm thu chức năng chỉ đọc. Chuẩn bị test cases từ báo cáo được phép dùng; dữ liệu test trong repo phải là dữ liệu tổng hợp, không copy toàn bộ inventory thực. Sau khi người dùng chỉ định host thử nghiệm và một thư mục thử nghiệm, kiểm chứng lần lượt HTTPS → login/logout → File Station metadata → nguồn metrics/storage được hỗ trợ. User/Group write, ACL write, firewall và storage mutations tiếp tục khóa.
