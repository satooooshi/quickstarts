
let data = [{"id":"111", "content":"example ticket"}]


// immutability
// https://noah.plus/blog/007/
export function addDetail(detail){
    // const newCatalog = [...data, product] // immutable
    data.push({id:detail.id, content:detail.content})
}

export function getDetailById(id){
    const res = data.filter(detail => detail.id === id )
    return res
}

