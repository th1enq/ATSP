# SDP không giao hoán và dựng cây từ đầu — 2026-10-11

## Phần mã đã bổ sung

- `scripts/sdp_barrier.py`: Newton với log-det barrier cho toàn bộ sáu affine LMIs, không cần các projector giao hoán. Số Decimal chỉ tìm ứng viên; khoảng trả về phải có primal hữu tỉ khả thi, dual PSD, stationarity đúng tuyệt đối và gap đạt accuracy.
- Sửa stationarity của dual sau làm tròn bằng bốn multiplier của các ràng buộc box. Nếu residual trên X là E, đặt `rho=max_i sum_j |E_ij|`, thêm `E+rho I` vào multiplier của box dưới và `rho I` vào box trên. Hai ma trận PSD và đóng residual chính xác. Làm tương tự với Y. Chuẩn hoá hệ số t trước bước này. Bộ replay không chạy Newton.
- `continuation_solver.py`: thử response đơn giản trước ellipsoid, nhưng chỉ nhận nếu **toàn bộ** separator chấp nhận. Response scalar được chọn sao cho X kế tiếp nằm trên lưới hữu tỉ cố định; không làm tròn trạng thái sau khi đã nhận response. Khi proposal không hợp lệ, vẫn dùng ellipsoid tổng quát.
- `continuation_state.py` và oracle: tái sử dụng phép tính cho các cạnh song song có cùng dữ liệu; không bỏ ràng buộc khác nhau.
- `general_sparsification.py --continuation-g`: chạy từ trạng thái ban đầu với g của thực nghiệm và lưu toàn bộ response. Origin là `instance-parameter-continuation`, khác nhánh tham số nguồn và terminal witness được cung cấp.
- `scripts/general_tree.py`: ghép nhiều bước, theo dõi ID cạnh qua mỗi đồ thị con, xuất cây cuối cùng và chứng nhận cut bound. `verify` kiểm tra lại cả chuỗi, các packing và cây cuối, không gọi solver để dựng lại.

## Vì sao cần nhánh tham số thực nghiệm

Với `t=1/(32(m+1))`, sau K bước:

` s_K = s_0 (1+t)^K ` và ` Q_K = Q_0 - 2 g r t K `.

Hai đại lượng này độc lập với response. Với tam giác 24 cạnh, `r=8`, cần **972 bước**. Tham số nguồn `g=1` làm `Q_K=-286/25`. Bất kỳ response nào cũng không sửa được sự cạn ngân sách này. Điều này không chứng minh đồ thị vô nghiệm: nhánh nguyên gốc dừng từ trước ở cutoff đủ lớn `R0=2^4097`.

Chế độ `instance` chọn g dyadic sao cho `g <= 1/(16 K t)`, nên lịch trình giữ ít nhất `7r/8` ngân sách Q. Đây là lựa chọn ngoài miền giả thiết của nguồn; không viện dẫn định lý tồn tại response cho g này. Mỗi response và chứng nhận terminal vẫn được kiểm tra trực tiếp. Mã có thể dừng với trạng thái incomplete khi không tìm được response.

Một bước mẫu tam giác với `g=1/64` đã đi đủ 972 response từ `X=L_H`, `s=1/2`, `Q=8`, kết thúc với `Q=6157/800`. Extraction lấy 6 cây; signing ứng viên giữ 6 cạnh và đầu ra đóng gói được 3 cây. File `triangle-three-from-initial.json` dùng phép ký dấu **certified-tree-candidate**, không phải descent Appendix A. Mẫu đường đi từ đầu dùng Appendix A, đã hoàn thành với `r_next=3`.

## SDP không giao hoán

`results/appendix-a-profile/noncommuting-barrier.json.gz` chứa 11 khoảng SDP đã chứng nhận, gồm ba truy vấn trực tiếp và tám truy vấn của signing Appendix A trên hai hướng không giao hoán:

| Accuracy yêu cầu | Gap hữu tỉ (xấp xỉ) | Newton steps | Thời gian (giây) |
|---|---:|---:|---:|
| 1/8 | 3,19e-4 | 57 | 1,003 |
| 1e-12 | 2,55e-15 | 146 | 2,602 |
| 1e-30 | 2,55e-33 | 291 | 6,574 |

Signing thực hiện hai bước, tám truy vấn, trả `[-1,+1]`, với bound squared `699175/1024`; khoảng 6,664 giây. Đây là một lần đo, không suy ra tốc độ cho kích thước lớn. Cả nhánh cùng ray lẫn nhiều ray trực giao đều từ chối mẫu này.

Sau lần đo này, endpoint search được sửa để so sánh **base.lower - candidate.upper**, rồi nhận coordinate đầu tiên đủ mức giảm. Hai dấu của coordinate vẫn được so sánh. Chứng nhận khoảng thực tế đã đủ để kết luận giảm potential; không cần dùng accuracy yêu cầu như một khoản phạt bổ sung, hoặc quét tất cả coordinate khi đã tìm được bước hợp lệ. Accuracy yêu cầu và kiểm tra final spectral bound vẫn được giữ.

## Mẫu tam giác với descent Appendix A

`results/general-sparsification/triangle-three-barrier.json` đã hoàn thành từ terminal witness: **42 truy vấn SDP**, tất cả có chứng nhận primal–dual; ký dấu giữ 7 cạnh, packing đầu ra có 3 cây. Construction mất **207,392 giây** trong lần đo với profiler và lưu chứng nhận. File `results/appendix-a-profile/triangle-three-barrier.json.gz` lưu cả 42 interval; không gọi ellipsoid. Đây là mốc không giao hoán với descent Appendix A, khác phép ký dấu ứng viên của mẫu continuation ban đầu.

Bản profiler ở mốc này ghi Newton steps trong trường `feasibility_calls`; mã hiện tại tách `newton_steps` khỏi số lần gọi ellipsoid. Bản dữ liệu lịch sử được giữ nguyên.

## Cây cuối từ trạng thái khởi đầu

`results/general-sparsification/triangle-three-tree.json` hoàn thành construction ở chế độ `instance`, không nhận terminal witness. Bộ dựng chọn `g=1/32`; 972 response đưa ngân sách tới `Q=2957/400`. Gradient frame và signing **Appendix A** giữ sáu cạnh; packing giảm 8→3. Cây cuối có ID gốc `[1,8]`, tương ứng cạnh `0–1` và `1–2`. Đây là luồng từ đầu với Appendix A, khác kết quả ký dấu ứng viên đã ghi ở trên.

Bộ replay kiểm tra cả 972 chuyển trạng thái, các LMIs, packing, lower frame covariance, signing, chuỗi ánh xạ cạnh và cây cuối. Cut ratio bound được báo là **1/4** đối với đa đồ thị đầu vào; cận này đến từ packing ban đầu, chưa phải cải thiện từ các epsilon rất lỏng. Không coi nó là thinness của một tour ATSP hay một bảo đảm trên TSPLIB.

Kiểm tra mã: **90 tests**: **89 đạt**, **1 test SciPy tùy chọn bỏ qua**. Replay độc lập: 11 khoảng SDP của mẫu hai ray, 42 khoảng của mẫu tam giác, chứng nhận một bước tam giác và chứng nhận cây cuối đều hợp lệ.

## Chạy lại

```sh
python3 benchmarks/bench_sdp_noncommuting.py \
  --output /tmp/noncommuting.json.gz
python3 scripts/check_sdp_value.py \
  results/appendix-a-profile/noncommuting-barrier.json.gz

python3 scripts/general_sparsification.py step \
  instances/general-sparsification/path-three.json \
  --continuation-g 1/64 --sdp-iteration-cap 0 --signing-cap 20 \
  --output /tmp/path-from-initial.json
python3 scripts/general_sparsification.py verify /tmp/path-from-initial.json

python3 scripts/general_tree.py build \
  instances/general-sparsification/triangle-three.json \
  --mode instance --sdp-iteration-cap 400 --seconds 360 \
  --output /tmp/triangle-tree.json
python3 scripts/general_tree.py verify /tmp/triangle-tree.json
```

## Phạm vi kết luận

Bộ giải generic đã có mã và chứng nhận hoạt động trên mẫu không giao hoán. Newton chưa có chứng minh thời gian đa thức hữu tỉ cho toàn bộ đầu vào; số học hữu hạn có thể không tìm ra proposal đủ tốt và khi đó báo lỗi rõ ràng, không gọi đó là vô nghiệm.

Các kết quả từ đầu dùng tham số thực nghiệm và đều dưới cutoff của nguồn. Cận epsilon của nguồn tại r nhỏ rất lỏng; việc hoàn thành construction không chứng minh thinness tốt hoặc xấp xỉ hằng số trên dữ liệu thực tế. Bộ dựng cây báo cả cận qua các vòng và cận đơn giản từ packing; có thể cận đơn giản mới là cận hữu ích hơn.

Chưa chạy lại TSPLIB trong đợt này, chưa có bằng chứng chất lượng vượt các số đo cũ. Việc chuyển từ graph explicit nhỏ sang số bản sao của HK lớn và một triển khai hiệu quả có bảo đảm phổ quát của paper vẫn là giới hạn thực tế.
