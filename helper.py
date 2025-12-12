def format_metadata_list_to_context(metadata_list):
    """
    Chuyển đổi danh sách metadata (List[Dict]) thành văn bản ngữ cảnh (String).
    """
    # Kiểm tra an toàn: Nếu input không phải list, bọc nó lại thành list
    if isinstance(metadata_list, dict):
        metadata_list = [metadata_list]
    
    if not metadata_list:
        return "Không có dữ liệu ngữ cảnh."
    
    full_context_text = ""
    metadata_list_result = []
    for m in metadata_list:
        metadata_list_result.append(m['metadata'])
    # Lặp qua từng hồ sơ trong danh sách
    for index, data in enumerate(metadata_list_result, 1):
        # 1. Trích xuất dữ liệu (Dùng .get để tránh lỗi nếu thiếu trường)
        ten = data.get('ten', 'Không rõ tên')
        mo_ta = data.get('mo_ta', '')
        
        # Nhóm thông tin phân loại
        loai_hinh = data.get('loai_hinh', 'N/A')
        chu_de = data.get('chu_de', 'N/A')
        dan_toc = data.get('dan_toc', 'N/A')
        
        # Nhóm thời gian & không gian
        nien_dai = data.get('nien_dai', 'N/A')
        thoi_ky = data.get('thoi_ky', 'N/A')
        vung_mien = data.get('vung_mien', 'N/A')
        dia_diem = data.get('dia_diem', 'N/A')
        
        # Nhóm giá trị nội dung
        y_nghia = data.get('y_nghia', '')
        tac_pham = data.get('nguyen_lieu_chinh', '') # Với Nguyễn Trãi là tác phẩm
        nhan_vat = data.get('nhan_vat_lien_quan', '')

        # 2. Tạo template văn bản cho TỪNG hồ sơ
        # Dùng dấu phân cách rõ ràng để Model không lẫn lộn giữa Sọ Dừa và Nguyễn Trãi
        profile_text = f"""
        ==================================================
        HỒ SƠ SỐ {index}: {ten.upper()}
        ==================================================
        
        [TỔNG QUAN]
        {mo_ta}
        
        [THÔNG TIN CHI TIẾT]
        - Phân loại: {loai_hinh} (Chủ đề: {chu_de})
        - Dân tộc: {dan_toc}
        - Thời gian: {nien_dai} ({thoi_ky})
        - Địa danh/Vùng miền: {vung_mien} - {dia_diem}
        
        [GIÁ TRỊ & LIÊN QUAN]
        - Tác phẩm/Di sản chính: {tac_pham}
        - Ý nghĩa: {y_nghia}
        - Nhân vật liên quan: {nhan_vat}
        """
        
        # 3. Ghép vào chuỗi tổng
        full_context_text += profile_text + "\n"

    return full_context_text

