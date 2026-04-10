$(document).ready(function(){

// ---------------- OWL ----------------
$('#slider1, #slider2, #slider3').owlCarousel({
    loop: true,
    margin: 20,
    responsiveClass: true,
    responsive: {
        0: { items: 2, nav: false, autoplay: true },
        600: { items: 4, nav: true, autoplay: true },
        1000: { items: 6, nav: true, loop: true, autoplay: true }
    }
});


// ---------------- PLUS CART ----------------
$(document).on('click', '.plus-cart', function(){
    var id = $(this).attr("pid").toString();
    var quantitySpan = $("#quantity-" + id);

    $.ajax({
        type: "GET",
        url: "/pluscart/",
        data: { prod_id: id },
        success: function(data){
            quantitySpan.text(data.quantity);
            $("#amount").text("Rs. " + data.amount);
            $("#totalamount").text("Rs. " + data.totalamount);
        }
    });
});


// ---------------- MINUS CART ----------------
$(document).on('click', '.minus-cart', function(){
    var id = $(this).attr("pid").toString();
    var quantitySpan = $("#quantity-" + id);

    $.ajax({
        type: "GET",
        url: "/minuscart/",
        data: { prod_id: id },
        success: function(data){
            quantitySpan.text(data.quantity);
            $("#amount").text("Rs. " + data.amount);
            $("#totalamount").text("Rs. " + data.totalamount);
        }
    });
});


// ---------------- REMOVE CART ----------------
$(document).on('click', '.remove-cart', function(e){
    e.preventDefault();

    var id = $(this).attr("pid").toString();
    var row = $(this).closest('.cart-item');

    $.ajax({
        type: "GET",
        url: "/removecart/",
        data: { prod_id: id },
        success: function(data){

            $("#amount").text("Rs. " + data.amount);
            $("#totalamount").text("Rs. " + data.totalamount);

            row.fadeOut(300, function(){
                $(this).remove();

                // if empty reload
                if ($('.cart-item').length === 0){
                    location.reload();
                }
            });
        }
    });
});

});